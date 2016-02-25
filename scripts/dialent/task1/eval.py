
import os

from dialent.standard import Standard
from dialent.task1.test import Test

from dialent.task1.util import loadAllStandard, loadAllTest

from dialent.common.evalmatrix import EvaluationMatrix
from dialent.common.metrics import Metrics

#########################################################################################

class Evaluator:
    """Response evaluator for the 1st track"""

    def __init__(self, is_locorg_enabled=True):
        """Create an object with or without the support for locorg objects"""
        self.is_locorg_enabled = is_locorg_enabled
        if is_locorg_enabled:
            self.tags = ['per', 'loc', 'org', 'locorg', 'overall']
        else:
            self.tags = ['per', 'loc', 'org', 'overall']

        self.metrics_dict = None


    def evaluate(self, std_path, test_path, output_path='', is_silent=False):
        """Run evaluation on all files in the given directories
        If output_path is provided, evaluation reports will be written there.
        is_silent determines if the result is printed to the output"""
        std = loadAllStandard(std_path)
        test = loadAllTest(test_path)

        diff = set([x.name for x in std]).symmetric_difference(
            set([y.name for y in test]))

        if len(diff) > 0:
            print('WARNING: missing files:')
            print('\n'.join(sorted(diff, key=lambda x: int(x[5:]))))

        std_by_name = dict([(x.name, x) for x in std])
        test_by_name = dict([(x.name, x) for x in test])
        names = sorted(set([x.name for x in std]).intersection(
            set([y.name for y in test])), key=lambda x: int(x[5:]))

        res = dict((tag, Metrics()) for tag in self.tags)

        for name in names:
            s = std_by_name[name]
            t = test_by_name[name]
            m = self.evaluateDocument(s, t)
            self.metrics_dict = dict((x, m[x]) for x in self.tags)
            self.printReport(s.name, output_path)
            for key in res:
                res[key].add(self.metrics_dict[key])
            
        if not is_silent:
            print(self.buildMetricsTable(res))

        return res

    def evaluateDocument(self, standard, test):
        """Run evaluation on the given standard and test markup"""
        s = standard.makeTokenSets(self.is_locorg_enabled)
        t = test.makeTokenSets(standard, self.is_locorg_enabled)

        em = EvaluationMatrix(s, t, TokenSetQualityCalculator())
        em.findSolution()
        self.em = em

        return em.metrics

    # Metrics and reports

    def buildMetricsTable(self, metrics_dict):
        """Build a table from the provided metrics for the output"""
        assert(len(metrics_dict.keys()) == len(self.tags))
        res = 'Type    ' + Metrics.header()
        for tag in self.tags:
            res += '\n{:8} '.format(tag) + metrics_dict[tag].toLine()

        return res

    def buildReport(self):
        """Builds a detailed comparison report"""
        res = ''
        res += '------STANDARD------\n'
        res += self.em.describeMatchingStd() + '\n\n';
        res += '--------TEST--------\n'
        res += self.em.describeMatchingTest() + '\n\n';
        res += '-------METRICS------\n'
        res += self.buildMetricsTable(
                self.metrics_dict
            )

        return res

    def printReport(self, name, out_dir):
        if len(out_dir) == 0:
            return

        is_perfect = self.em.metrics['overall'].f1 == 1.0
        os.makedirs(out_dir, exist_ok=True)

        filename = ('' if is_perfect else '_') +  name + '.report.txt'
        with open(os.path.join(out_dir, filename), 'w', encoding='utf-8') as f:
            f.write(self.buildReport())


#########################################################################################

class TokenSetQualityCalculator:
    """Calculates preliminary and final quality for TokenSet objects"""

    tag_table = {
        ('per', 'per') : 1, ('per', 'org') : 0, ('per', 'loc') : 0, ('per', 'locorg') : 0,
        ('org', 'per') : 0, ('org', 'org') : 1, ('org', 'loc') : 0, ('org', 'locorg') : 0,
        ('loc', 'per') : 0, ('loc', 'org') : 0, ('loc', 'loc') : 1, ('loc', 'locorg') : 0,
        ('locorg', 'per') : 0, ('locorg', 'org') : 0, ('locorg', 'loc') : 0, ('locorg', 'locorg') : 1
    }

    def tagMultiplier(self, s, t):
        return TokenSetQualityCalculator.tag_table[(s.tag, t.tag)]
    
    def evaluate(self, pairs, unmatched_std, unmatched_test):
        """Evaluate the matching. Returns metrics"""
        matching = {}
        for s, t in pairs:
            matching[s] = t
            matching[t] = s

        tp = 0
        n_relevant_pairs = 0
        matched_std_objects = set()
        for s, t in pairs:
            if not self.isIgnored(s, t, matching):
                tp += self.quality(s, t)
                matched_std_objects.add(s)
                n_relevant_pairs += 1

        # in this task no unmatched test object can be ignored
        n_test = n_relevant_pairs + len(unmatched_test)

        n_std = n_relevant_pairs
        for obj in unmatched_std:
            if not obj in matched_std_objects:
                if not self.isStandardIgnored(obj, matching):
                    n_std += 1

        return Metrics.createSimple(tp, n_std, n_test)

    def priority(self, s, t):
        """Calculate preliminary quality that goes into the optimization table"""
        multiplier = self.tagMultiplier(s,t)
        if multiplier == 0:
            return 0

        tp = len(s.tokens.intersection(t.tokens))
        fn = len(s.tokens.difference(t.tokens))
        fp = len(t.tokens.difference(s.tokens))
        
        summ = tp + fp + fn
        assert(summ > 0)
        return multiplier * tp / summ if summ > 0 else 0

    def quality(self, s, t):
        """Calculate final quality that is maximized during the matching optimization"""
        multiplier = self.tagMultiplier(s,t)
        if multiplier == 0:
            return 0

        tokens_tp = s.tokens.intersection(t.tokens)
        tokens_fn = s.tokens.difference(t.tokens)
        
        tp = 0.0
        for token in tokens_tp:
            tp += s.mark(token) # there can be no punctuation here

        fn = 0.0
        for token in tokens_fn:
            # in case some punctuation did end up in the standard markup somehow
            # (which apparently happens)
            fn += s.mark(token) if not token.isPunctuation() else 0
                
        fp = len(t.tokens.difference(s.tokens))
        
        summ = tp + fp + fn

        # summ can be equal to zero in cases when the mention has no 'priority' spans like
        # org_name. In these cases, we will just compare the annotations with no weights
        return multiplier * tp / summ if summ > 0 else self.priority(s,t)
    
    def isIgnored(self, s, t, matching):
        """Check if the matched pair of (s, t) should be ignored within the current
        matching"""


        return self.isStandardIgnored(s, matching)

    def isStandardIgnored(self, s, matching):
        """Check if the given standard object should be ignored within the current
        matching"""

        # unnamed objects are ignored regardless of their matching status
        if s.isUnnamed():
            return True
        
        # embedded objects are ignored regardless of their matching status
        if len(s.parents) > 0:
            return True

        # sibling object processing logic
        assert(len(s.siblings) <= 1)
        for sibling in s.siblings:
#            assert(set([sibling.tag, s.tag]) == set(['org', 'loc']))
            if (s in matching) == (sibling in matching):
                # when both or neither are matched, ignore the non-organization
                # in case of both being organizations, use any of them
                if sibling.tag == s.tag:
                    if s.is_ignored_sibling:
                        return True
                    else:
                        sibling.is_ignored_sibling = True
                        return False
                else:
                    assert('org' in [sibling.tag, s.tag])
                    return s.tag != 'org'
            else:
                # otherwise ignore the unmatched sibling
                return not (s in matching)


        return False

    def isTestIgnored(self, t, matching):
        """Check if the given standard object should be ignored within the current
        matching"""

        # in this track no test object can be ignored
        return False