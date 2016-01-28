# this module contains evaluation logic for the 2nd task

import os

from dialent.common.evalmatrix import EvaluationMatrix
from dialent.common.metrics import Metrics

from dialent.standard import Standard
from dialent.task2.test import Test

from dialent.task2.util import loadAllStandard, loadAllTest

#########################################################################################

class Evaluator:
    """Performs evaluation for the second task
    Can run comparison in two modes:
     - regular: unmatched values in test markup are considered undesirable and affect the
       score in a negative way
     - simple: unmatched values in test do not affect the score"""

    stat_tags = ['per', 'loc', 'org', 'overall']

    def __init__(self, mode='regular'):
        """Initialize the object"""
        assert(mode == 'regular' or mode == 'simple')
        self.mode = mode


    def evaluate(self, std_path, test_path, output_path=''):
        """Run evaluation on all files in the given directories"""
        std = loadAllStandard(std_path)
        test = loadAllTest(test_path)

        diff = set([x.name for x in std]).symmetric_difference(
            set([y.name for y in test]))

        assert(len(diff) == 0)
        res = []
        for tag in Evaluator.stat_tags:
            res.append(Metrics())

        for i, s in enumerate(std):
            if not s.has_coref:
                # do not compare documents without a .coref file
                # this is just for convenience
                continue
            m_tuple = self.evaluateDocument(s, test[i])
            self.printReport(s.name, output_path)
            for i, val in enumerate(res):
                val.add(m_tuple[i])
            
        print(self.buildMetricsTable(res))

    def evaluateByDocument(self, std_path, test_path):
        """Run evaluation on all files in the given directories. Print output by
        document"""
        std = loadAllStandard(std_path)
        test = loadAllTest(test_path)

        diff = set([x.name for x in std]).symmetric_difference(
            set([y.name for y in test]))

        assert(len(diff) == 0)

        for i, s in enumerate(std):
            res = self.evaluateDocument(s, test[i])
            print('\n' + s.name)
            print('Type    ' + Metrics.header())
            for i, tag in enumerate(Evaluator.stat_tags):
                print('{:8} '.format(tag.upper()) + res[i].toLine())
            
    def evaluateDocument(self, s, t):
        """Compare standard markup s with test markup t and evaluate T.
        Returns the typical metrics tuple"""

        em = EvaluationMatrix(s.entities, t.entities,
                 EntityQualityCalculator(forgive_extra_values = (self.mode=='simple')))
        em.findSolution()
        self.em = em

        self.metrics_tuple = (em.metrics['per'], em.metrics['loc'],
                em.metrics['org'], em.metrics['overall'])
        self.metrics_list = list(self.metrics_tuple)

        return self.metrics_tuple

    # Metrics and reports

    def buildMetricsTable(self, metrics_list):
        """Build a table from the provided metrics for the output"""
        assert(len(metrics_list) == len(Evaluator.stat_tags))
        res = 'Type    ' + Metrics.header()
        for i, tag in enumerate(Evaluator.stat_tags):
            res += '\n{:8} '.format(tag.upper()) + metrics_list[i].toLine()

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
                self.metrics_list
            )

        return res

    def printReport(self, name, out_dir):
        if len(out_dir) == 0:
            return

        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, name + '.report.txt'), 'w', encoding='utf-8') as f:
            f.write(self.buildReport())

        
#########################################################################################

class EntityQualityCalculator:
    """Calculates entity matching quality and priority"""

    tag_table = {
        ('per', 'per') : 1, ('per', 'org') : 0, ('per', 'loc') : 0, ('per', 'locorg') : 0,
        ('org', 'per') : 0, ('org', 'org') : 1, ('org', 'loc') : 0, ('org', 'locorg') : 0,
        ('loc', 'per') : 0, ('loc', 'org') : 0, ('loc', 'loc') : 1, ('loc', 'locorg') : 0,
        ('locorg', 'per') : 0, ('locorg', 'org') : 0, ('locorg', 'loc') : 0, ('locorg', 'locorg') : 1
    }

    def __init__(self, forgive_extra_values=False):
        """Make a new calculator. If forgive_extra_values is True, there will be no
        penalty for any additional values in test"""
        self.forgive_extra_values = forgive_extra_values


    def tagMultiplier(self, s, t):
        return EntityQualityCalculator.tag_table[(s.tag, t.tag)]


    def priority(self, s, t):
        """Calculates preliminary quality that goes into the table"""
        multiplier = self.tagMultiplier(s,t)
        if multiplier == 0:
            return 0

        return multiplier * self.quality(s, t)


    def quality(self, s, t):
        """Calculates final quality that is maximized during the search for the optimal
        matching"""

        unmatched_std = set(s.attributes)
        matched_std = set()
        unmatched_test = set(t.attributes)
        matched_test = set()
        intersection_size = 0
        for t_attr in t.attributes:
            for s_attr in s.attributes:
                if s_attr.matches(t_attr):
                    matched_std.add(s_attr)
                    matched_test.add(t_attr)

                    if s_attr in unmatched_std:
                        unmatched_std.remove(s_attr)
                    if t_attr in unmatched_test:
                        unmatched_test.remove(t_attr)

        tp = len(matched_std)
        fp = len(unmatched_test) if not self.forgive_extra_values else 0
        fn = len(unmatched_std)

        d = float(tp + fn + fp)

        return (tp / d) if d > 0 else 0.0