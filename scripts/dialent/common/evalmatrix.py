
import numpy as np

from dialent.common.metrics import Metrics

#########################################################################################

class TagData:
    """Utility object that contains data regarding a set of objects currently processed
    by EvaluationMatrix"""

    def __init__(self, tag, object_list):
        """Loads an object list with the given tag from the larger object_list"""
        self.tag = tag
        self.objects = sorted([x for x in object_list if x.tag == tag],
                              key=lambda x: x.id)
        self.size = len(self.objects)
        self._start = 0

    def start(self):
        return self._start

    def end(self):
        return self._start + self.size


class EvaluationMatrix:
    """Matrix built out of object pair quality that finds an optimal matching"""

    allowed_tags = ['per', 'loc', 'org', 'locorg']

    def __init__(self, std, test, calc, mode='regular'):
        """Initialize the matrix.
        
        std and test must be lists of objects from standard and test respectively
        mode must be either 'regular' or 'simple' and it determines whether locorgs are
        matched with orgs and locs or not
        calc must be a priority/quality calculator object used in the task at hand"""

        assert(mode == 'regular' or mode == 'simple')
        self.mode = mode
        self.metrics = {}

        self.s = {}
        self.t = {}
        for tag in EvaluationMatrix.allowed_tags:
            self.s[tag] = TagData(tag, std)
            self.t[tag] = TagData(tag, test)

        # finalize the offsets
        for i in range(1, len(EvaluationMatrix.allowed_tags)):
            prev_tag = EvaluationMatrix.allowed_tags[i-1]
            tag = EvaluationMatrix.allowed_tags[i]
            self.s[tag]._start = self.s[prev_tag].end()
            self.t[tag]._start = self.t[prev_tag].end()

        self.std = []
        self.test = []
        for tag in EvaluationMatrix.allowed_tags:
            self.std.extend(self.s[tag].objects)
            self.test.extend(self.t[tag].objects)

        self.n_std = len(self.std)
        self.n_test = len(self.test)

        self.m = np.zeros((self.n_std, self.n_test))
        self.calc = calc

        for i, x in enumerate(self.std):
            for j, y in enumerate(self.test):
                self.m[i][j] = self.calc.priority(x, y)

    def findSolution(self):
        """Runs the recursive search to find an optimal matching"""
        
        q, pairs = self._recursiveSearch(
            [i for i in range(self.n_std)],
            [j for j in range(self.n_test)],
            []
            )

        self.metrics['overall'] = self._evaluate(pairs)
        for tag in EvaluationMatrix.allowed_tags:
            self.metrics[tag] = self._evaluate(pairs, tag)

        # save matching data
        self.logMatching(pairs)

        return pairs

    def logMatching(self, pairs):
        """Saves matching data"""
        self.matching = {}
        self.matched_std = []
        self.matched_test = []
        for i, j in pairs:
            s = self.std[i]
            t = self.test[j]
            self.matching[s] = t
            self.matching[t] = s
            self.matched_std.append(s)
            self.matched_test.append(t)
        self.unmatched_std = [s for s in self.std if not s in self.matched_std]
        self.unmatched_test = [t for t in self.test if not t in self.matched_test]

    def describeMatchingStd(self):
        """Builds a detailed matching description for standard objects"""
        return self._doDescribeMatching(self.matched_std, self.unmatched_std, False)

    def describeMatchingTest(self):
        """Builds a detailed matching description for test objects"""
        return self._doDescribeMatching(self.matched_test, self.unmatched_test, True)

    def _doDescribeMatching(self, matched, unmatched, is_swapped):
        """Builds a detailed matching description with the given lookup tables"""
        res = ''
        for x in matched:
            y = self.matching[x]
            pair = (y, x) if is_swapped else (x, y)
            is_ignored = self.calc.isIgnored(pair[0], pair[1], self.matching)
            q = self.calc.quality(*pair)
            res += '{}\t{}\t=\t{}\n'.format('{:7.2f}'.format(q)
                                            if not is_ignored
                                            else 'IGNORED',
                    x.toInlineString(), y.toInlineString())

        res += '\n'
        for x in unmatched:
            is_ignored = (self.calc.isTestIgnored(x, self.matching)
                          if is_swapped
                          else self.calc.isStandardIgnored(x, self.matching))
            res += '{} {}\n'.format('{:7.2f}'.format(0.0)
                                    if not is_ignored
                                    else 'IGNORED',
                    x.toInlineString())

        return res

    def _recursiveSearch(self, std, test, pairs):
        """
            Run a recursive search of the optimal matching.

            Returns the following tuple: (overall quality, matching)

            std - remaining standard indices list
            test - remaining test indices list
            pairs - current list of built pairs
        """
        if len(std) == 0 or len(test) == 0:
            # final step, evaluate the matching
            metrics = self._evaluate(pairs)
            return metrics.f1, pairs

        curr = std[0]
        max_res = None

        possible_pairs_count = 0
        pair_max_alternatives = 0

        options, has_perfect_match = self._findMatches(curr, test)
        for t in options:
            i = test.index(t)

            # let's see what other matching options does this test object have
            # this is necessary to check conditions for the logic below
            alt_count = 0
            skip_test_object = False
            for k in std[1:]:
                if self.m[k, t] == 1.0 and self.m[curr, t] < 1.0:
                    # test objects that have some other perfect matching must be skipped
                    skip_test_object = True
                if self.m[k, t] != 0.0:
                    alt_count += 1
                if alt_count > pair_max_alternatives:
                    pair_max_alternatives = alt_count
                
            if skip_test_object:
                continue
            else:
                possible_pairs_count += 1


            # try to confirm the pair
            res = self._recursiveSearch(
                std[1:], test[:i] + test[i+1:],
                pairs + [(curr, t)])
            if max_res is None or res[0] > max_res[0]:
                max_res = res

        # check what would happen if this standard object were ignored
        # this check is obviously performance-heavy and only necessary under
        # these conditions
        if (possible_pairs_count == 0
                or possible_pairs_count == 1
                    and pair_max_alternatives > 0
                    and not has_perfect_match):
            res = self._recursiveSearch(
                std[1:], test,
                pairs)
            if max_res is None or res[0] > max_res[0]:
                max_res = res

        return max_res

    def _findMatches(self, s_index, test):
        """Finds a list of possible matches for the standard object with the given index
        within the list of available test objects.
        
        Returns a list of test object indices
        
        According to the documentation, any perfectly fitting objects MUST be matched"""
        perfect_matches = [t for t in test if self.m[s_index, t] == 1.0]
        matches = [t for t in test if self.m[s_index, t] > 0.0] 
        if len(perfect_matches) > 0:
            return perfect_matches, True
        else:
            return matches, False

    def _evaluate(self, pairs, tag_filter = ''):
        matched_std = set(self.std[_s] for _s,_t in pairs)
        matched_test = set(self.test[_t] for _s,_t in pairs)
        
        if tag_filter in EvaluationMatrix.allowed_tags:
            subset = self._reduce(pairs, tag_filter)
        else:
            subset = pairs

        unmatched_std = [s for s in self.std if not (s in matched_std)]
        unmatched_test = [t for t in self.test if not (t in matched_test)]

        # unmatched_test must contain all objects of the given tag that were not in ANY
        # pair, including cases where a locorg was matched to an loc, for example
        if tag_filter in EvaluationMatrix.allowed_tags:
            unmatched_std = [s for s in unmatched_std if s.tag == tag_filter]
            unmatched_test = [t for t in unmatched_test if t.tag == tag_filter]

        # replace indices with actual objects for evaluation
        actual_pairs = [(self.std[_s], self.test[_t]) for _s,_t in subset]

        return self.calc.evaluate(actual_pairs, unmatched_std, unmatched_test)

    def _reduce(self, matching, tag):
        """Returns a sub-matching corresponding to the given tag"""
        res = []
        for _s, _t in matching:
            if _s >= self.s[tag].start() and _s < self.s[tag].end():
                res.append((_s, _t))
        return res