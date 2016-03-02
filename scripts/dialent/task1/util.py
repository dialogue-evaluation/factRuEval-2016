# This module contains two utilities for the first track:
#   - evaluator
#   - automatic response generator

#########################################################################################

import os
import numpy as np

import re

from dialent.config import Config
from dialent.config import Tables

from dialent.standard import Standard
from dialent.task1.test import Test

#########################################################################################

class ResponseGenerator:
    """
        Objects of this class generate responses based on the standard markup.
        It's mostly used for evaluator testing
    """
    
    def __init__(self, is_locorg_allowed=True):
        """
            Creates an instance of an object.
        
            is_locorg_allowed - enable/disable 'LocOrg' tag
        """
        
        self.is_locorg_allowed = is_locorg_allowed
    

    def generate(self, std_dir, out_dir):
        """
            Generate a response based on all the standard documents in the directory

            std_dir - standard markup directory
            out_dir - directory where the generated response will be saved to
        """

        unique_names = set()

        for filename in os.listdir(std_dir):
            parts = filename.split('.')
            unique_names.add('.'.join(parts[:-1]))

        names = list(unique_names)
        for name in names:
            std = Standard(name, std_dir)
            self.generateDoc(std, os.path.join(out_dir, name + '.task1'))

    
    def generateDoc(self, standard, out_filename):
        """
            Generate a response based on the provided standard markup.

            standard - loaded standard markup
            out_filename - destination filename
        """
        
        s = standard.makeTokenSets(self.is_locorg_allowed)

        allowed_tags = ['per', 'org', 'loc']
        if self.is_locorg_allowed:
            allowed_tags.append('locorg')
            
        res = ''
        for tag in allowed_tags:
            res += self._doBuildResponse(tag, [x for x in s if x.tag == tag])
        
        os.makedirs(os.path.dirname(out_filename), exist_ok=True)
        with open(out_filename, 'w') as f:
            f.write(res)
        
                
    def _doBuildResponse(self, tag, token_sets):
        """
            Build a partial response assotiated with the given tag

            tag - mention type tag
            token_sets - a list of TokenSet objects of the given tag
        """
        intervals = [x.toInterval() for x in token_sets]
        return '\n'.join(
            ['{} {} {}'.format(tag, x.start, x.length) for x in intervals]
        ) + '\n'


#########################################################################################

summary_header_template = '{:8} {:8} {:8} {:8} {:8} {:8} {:8}'
summary_line_template = '{:8} {:8.4f} {:8.4f} {:8.4f} {:8.2f} {:8.0f} {:8.0f}'

class Evaluator:
    """
        Response evaluator for the 1st track
    """

    def evaluate(self, std_dir, test_dir, is_locorg_allowed=True):
        """
            Run the evaluation of the provided response, and print the overall result

            std_dir - standard markup files directory
            test_dir - responese directory
            is_locorg_allowed - enables/disables 'locorg' mention type
        """

        res,tmp = self._doEvaluate(std_dir, test_dir, is_locorg_allowed)
        print(summary_header_template.format(
            'Type', 'P', 'R', 'F1', 'TP', 'In Std.', 'In Test.'))

        tp = 0
        n_std = 0
        n_test = 0

        for key in sorted(res.keys()):
            print(summary_line_template.format(key, *res[key]))
            tp += res[key][3]
            n_std += res[key][4]
            n_test += res[key][5]

        overall = calcMetrics(tp, n_std, n_test)
        print('')
        print(summary_line_template.format('Overall', *overall))
        

    def resultByDocument(self, std_dir, test_dir, is_locorg_allowed=True):
        """
            Run the evaluation of the provided response, and print the result for every
            document.

            std_dir - standard markup files directory
            test_dir - responese directory
            is_locorg_allowed - enables/disables 'locorg' mention type
        """

        tmp,dct = self._doEvaluate(std_dir, test_dir, is_locorg_allowed)
        names = list(dct.keys())
        
        # determine the allowed tags
        allowed_tags = ['per', 'org', 'loc']
        if is_locorg_allowed:
            allowed_tags.append('locorg')
            
        # build the results table
        lst = []
        for name in names:
            line = [name]
            for tag in allowed_tags:
                vals = dct[name][tag]
                line.append('{:3.2f} / {:3.2f} / {:3.2f} / {:4.1f} / {:3} / {:3}'.format(
                    *vals))
            lst.append(line)
            
        # print stuff
        lst = sorted(lst, key=lambda x: int(x[0][5:]))

        print('     '.join(['{:10}'.format('')]
                         + ['{:37}'.format(x) for x in allowed_tags]))
        for line in lst:
            print('     '.join(['{:10}'.format(line[0])]
                         + ['{:37}'.format(x) for x in line[1:]]))        
    
    def _doEvaluate(self, std_dir, test_dir, is_locorg_allowed=True):
        """
            Evaluate the submission by comparing it to the standard

            Returns a dictionary of metrics by mention type.
            Metrics include precision, recall, f1,
            true positive count, standard size and test size
            in that order.

            std_dir - standard markup files directory
            test_dir - response files directory
            is_locorg_allowed - enables/disables 'locorg' mention type
        """
        
        unique_names = set()

        for filename in os.listdir(std_dir):
            parts = filename.split('.')
            unique_names.add('.'.join(parts[:-1]))

        names = list(unique_names)
        
        for filename in os.listdir(test_dir):
            parts = filename.split('.')
            if parts[-1] != 'task1':
                continue
            unique_names.remove('.'.join(parts[:-1]))
            
        # validate the submission integrity:
        if len(unique_names) > 0:
            raise Exception('Missing files in the response:\n'
                            + '\n'.join(sorted(unique_names)))
        
        allowed_tags = ['per', 'org', 'loc']
        if is_locorg_allowed:
            allowed_tags.append('locorg')
            
        doc_results = {}
        # calculate partial metrics:
        tp = dict([(x, 0.0) for x in allowed_tags])
        n_std = dict([(x, 0.0) for x in allowed_tags])
        n_test = dict([(x, 0.0) for x in allowed_tags])
        for name in names:
            std = Standard(name, std_dir)
            test = Test(name, test_dir)
            res = self.evaluateDocument(std, test, is_locorg_allowed)
            doc_results[name] = res
            for tag in allowed_tags:
                tp[tag] += res[tag][3]
                n_std[tag] += res[tag][4]
                n_test[tag] += res[tag][5]
                
        # calculate global metrics:
        return dict([(tag, calcMetrics(tp[tag], n_std[tag], n_test[tag]))
                   for tag in allowed_tags]), doc_results
    

    def evaluateDocument(self, standard, test, is_locorg_allowed=True):
        """
            Compare the provided standard and test markup.

            Returns a dictionary of metrics by mention type.
            Metrics include precision, recall, f1,
            true positive count, standard size and test size
            in that order.

            standard - loaded standard document
            test - loaded test document
            is_locorg_allowed - enables/disables 'locorg' mention type
        """
        s = standard.makeTokenSets(is_locorg_allowed)
        t = test.makeTokenSets(standard, is_locorg_allowed)

        allowed_tags = ['per', 'org', 'loc']
        if is_locorg_allowed:
            allowed_tags.append('locorg')

        return dict([(x, self.doCompareTag(s[x], t[x])) for x in allowed_tags])

    def doCompareTag(self, std, test):
        """
            Compare two lists of TokenSet objects

            Returns metrics tuple.
            The tuple includes precision, recall, f1,
            true positive count, standard size and test size
            in that order.
        
            std - list of TokenSet objects from the standard markup
            test - list of TokenSet objects from the test markup
        """
        optimizer = MatchingOptimizer(std, test)
        return optimizer.findBestResult()


#########################################################################################

class MatchingOptimizer:
    """Finds the best possible matching for the given standard and test."""

    def __init__(self, std, test):
        """Initialize the object.
            
        std - list of TokenSets provided by the standard markup
        test - list of TokenSets provided by the test markup."""            

        self.std = std
        self.test = test

        n_std = len(std)
        n_test = len(test)
        self.m = np.zeros((n_std, n_test))

        # fill the bipartite graph cost matrix
        for i, s in enumerate(std):
            for j, t in enumerate(test):
                if s.intersects(t):
                    self.m[i, j] = self._calculatePairPriority(std[i], test[j])


    def findBestResult(self):
        """Find and evaluate the best possible matching"""

        # find the maximum matching
        # uses naive search due to matrix sparcity,
        # as well as scipy 0.17 being unavailable :(

        s_ind = [i for i,x in enumerate(self.std)]
        t_ind = [i for i,x in enumerate(self.test)]

        return self._recursiveSearch(s_ind, t_ind, [])


    def _evaluatePairs(self, pairs):
        """Run an evaluation of the provided set of pairs.
        
        Returns the usual metrics tuple"""

        tp = 0
        matched_std_objects = set()
        for i, j in pairs:
            tp += self._calculatePairQuality(self.std[i], self.test[j])
            matched_std_objects.add(self.std[i])

        n_test = len(self.test)

        n_std = 0
        for obj in self.std:
            is_relevant = True
            if not obj in matched_std_objects:
                # this is the logic used to skip unmatched embedded organizations in the
                # standard markup, but only if the larger organization is correctly
                # matched
                for parent in obj.parents:
                    if parent in matched_std_objects:
                        is_relevant = False

                # alternatively, check if the object has no valuable spans
                # unmatched objects with no spans marked by a positive number 
                total_mark = sum([obj.mark(token) for token in obj.tokens])
                if total_mark == 0.0:
                    is_relevant = False

            if is_relevant:
                n_std += 1
        
        return calcMetrics(tp, n_std, n_test)

    def _findMatches(self, s_index, test):
        """Finds a list of possible matches for the standard object with the given index
        within the list of available test objects.
        
        Returns a list of test object indices
        
        According to the documentation, any perfectly fitting objects MUST be matched"""
        perfect_matches = [t for t in test if self.m[s_index, t] == 1]
        matches = [t for t in test if self.m[s_index, t] != 0] 
        return perfect_matches if len(perfect_matches) > 0 else matches


    def _recursiveSearch(self, std, test, pairs):
        """
            Run a recursive search of the maximum matching.

            Returns the standard metrics tuple

            m - cost matrix
            std - standard indices list
            test - test indices list
            pairs - current list of built pairs
        """
        if len(std) == 0 or len(test) == 0:
            # final step, evaluate the matching
            return self._evaluatePairs(pairs)

        curr = std[0]
        max_res = None

        possible_pairs_count = 0
        pair_max_alternatives = 0

        for t in self._findMatches(curr, test):
            i = test.index(t)

            # let's see what other matching options does this test object have
            # this is necessary to check conditions for the logic below
            possible_pairs_count += 1
            alt_count = 0
            skip_test_object = False
            for k in std:
                if self.m[k, t] == 1 and self.m[curr, t] < 1:
                    # test objects that have some other perfect matching must be skipped
                    skip_test_object = True
                if self.m[k, t] != 0:
                    alt_count += 1
                if alt_count > pair_max_alternatives:
                    pair_max_alternatives = alt_count
                
            if skip_test_object:
                continue

            # try to confirm the pair
            res = self._recursiveSearch(
                std[1:], test[:i] + test[i+1:],
                pairs + [(curr, t)])
            if max_res is None or res[2] > max_res[2]:
                max_res = res

        # check what would happen if this standard object were ignored
        # this check is obviously performance-heavy and only necessary under
        # these conditions
        if (possible_pairs_count == 0 or
                possible_pairs_count == 1 and pair_max_alternatives > 1):
            res = self._recursiveSearch(
                std[1:], test,
                pairs)
            if max_res is None or res[2] > max_res[2]:
                max_res = res

        return max_res    


    # utility methods

    def _calculatePairPriority(self, s, t):
        """Calculate the preliminary quality of a matched pair"""
        tp = len(s.tokens.intersection(t.tokens))
        fn = len(s.tokens.difference(t.tokens))
        fp = len(t.tokens.difference(s.tokens))
        
        summ = tp + fp + fn
        assert(summ > 0)
        return tp / summ if summ > 0 else 0
    
    def _calculatePairQuality(self, s, t):
        """Calculate the final quality of a matched pair"""

        tokens_tp = s.tokens.intersection(t.tokens)
        tokens_fn = s.tokens.difference(t.tokens)
        
        tp = 0.0
        for token in tokens_tp:
            tp += s.mark(token)

        fn = 0.0
        for token in tokens_fn:
            fn += s.mark(token)
                
        fp = len(t.tokens.difference(s.tokens))
        
        summ = tp + fp + fn

        # summ can be equal to zero in cases when the mention has no 'priority' spans like
        # org_name. In these cases, we will just compare the annotations with no weights
        return tp / summ if summ > 0 else self._calculatePairPriority(s,t)


def calcMetrics(tp, n_std, n_test):
    """Calculate precision, recall and f1"""

    # default precision and recall are set to 1
    # because technically an empty test corresponding to an empty standard
    # should be the correct answer
    precision = (tp / float(n_test)) if n_test > 0 else 1
    recall = (tp / float(n_std)) if n_std > 0 else 1
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return (precision, recall, f1, tp, n_std, n_test)

#########################################################################################
# Misc.

def loadAllStandard(path):
    """Load all standard markup files from the provided directory. Returns a list."""

    names = set([x.split('.')[0] for x in os.listdir(path)])
    res = []
    for name in names:
        if re.match('book_[0-9]+', name) == None:
            continue
        res.append(Standard(name, path))
    
    return sorted(res, key=lambda x: int(x.name[5:]))   # book_XXX - sort by number

def loadAllTest(path):
    """Load all test markup files from the provided directory. Returns a list"""
    names = set(x.split('.')[0] for x in os.listdir(path) if '.task1' in x)
    res = [Test(name, path) for name in names]
    
    return sorted(res, key=lambda x: int(x.name[5:]))   # book_XXX - sort by number
