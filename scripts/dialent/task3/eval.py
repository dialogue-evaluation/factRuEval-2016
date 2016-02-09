
import os

from dialent.config import Tables

from dialent.standard import Standard
from dialent.task3.test import Test

from dialent.objects import Fact
from dialent.common.metrics import Metrics

from dialent.task3.util import loadAllStandard
from dialent.task3.util import loadAllTest

#########################################################################################

class Evaluator:
    """Evaluates the task 3 responses"""

    def __init__(self, hard_mode=False):
        self.hard_mode = hard_mode

    def evaluate(self, std_path, test_path, output_path):
        print('Running evaluation, this might take a while...')
        std = loadAllStandard(std_path)
        test = loadAllTest(test_path)
        
        diff = set([x.name for x in std]).symmetric_difference(
            set([y.name for y in test]))

        assert(len(diff) == 0)
        res = Metrics()

        for i, s in enumerate(std):
            if not s.has_facts:
                # do not compare documents without a .facts file
                # this is just for convenience
                continue
            metrics = self.evaluateDocument(s, test[i])
            self.printReport(s.name, output_path)
            res.add(metrics)
            
        print(Metrics.header())
        print(res.toLine())

    def evaluateDocument(self, std, test):
        self.optimizer = Optimizer(std, test, self.hard_mode)
        self.optimizer.findSolution()
        
        return self.optimizer.metrics

    def printReport(self, name, out_dir):
        """Print a detailed report on the document evaluation"""
        if len(out_dir) == 0:
            return

        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, name + '.report.txt'), 'w', encoding='utf-8') as f:
            f.write(self.optimizer.describeMatching())

class Optimizer:
    """Optimizes the matching"""

    def __init__(self, std, test, hard_mode):
        self.test = test.facts
        self.hard_mode = hard_mode

        if hard_mode:
            # hard mode, remove all facts with modality other than 'actual'
            self.std = [x for x in std.facts if not x.has_easymode_modality]
        else:
            # easy mode, ignore all facts marked as difficult, and remove phase argument
            self.std = std.facts
            for fact in self.std:
                if fact.has_hardmode_difficulty:
                    fact.is_ignored = True
                fact.removePhase()

        self.findPossibleMatches()

    def findPossibleMatches(self):
        """Initialize the compatability table of test and standard objects"""
        self.possible_matches = []
        for t in self.test:
            self.possible_matches.append([s for s in self.std if s.canMatch(t)])

    def findSolution(self):
        self.metrics, self.clusters = self.recursiveSearch(self.test, self.possible_matches, [])

    def recursiveSearch(self, test, matches, indices):
        if len(test) == 0:
            assert(len(indices) == len(self.test))
            self.clusters = self.buildClusters(indices)
            self.metrics = self.evaluate(self.clusters)
            return self.metrics, self.clusters

        m_best, c_best = None, []
        t = test[0]
        index = self.test.index(t)
        for s in matches[0]:
            m, c = self.recursiveSearch(test[1:], matches[1:], indices + [self.std.index(s)])
            if m_best == None or m_best.f1 < m.f1:
                m_best, c_best = m, c
        
        # What would happen if the object was skipped entirely?
        m, c = self.recursiveSearch(test[1:], matches[1:], indices + [-1])
        if m_best == None or m_best.f1 < m.f1:
            m_best, c_best = m, c
            
        return m_best, c_best

    def buildClusters(self, indices):
        """Build a collection of clusters according to the indices of standard objects
        test objects were matched with"""

        std_to_cluster = dict([(s, Cluster.unpairedStandard(s)) for s in self.std])
        test_clusters = []

        for i, t in enumerate(self.test):
            if indices[i] == -1:
                test_clusters.append(Cluster.unpairedTest(t))
                continue
            
            s = self.std[indices[i]]
            std_to_cluster[s].add(t)

        return [std_to_cluster[s] for s in self.std] + test_clusters

    def evaluate(self, clusters):
        """Evaluate a set of clusters"""
        q_std = dict([(s,-1) for s in self.std])
        q_test = dict([(t,-1) for t in self.test])

        for c in clusters:
            c.calculateQuality()
            q_std[c.std] = c.quality
            for t in c.test:
                assert(q_test[t] == -1)
                q_test[t] = c.quality

        assert(not -1 in q_std.values())
        assert(not -1 in q_test.values())

        tp_std = sum(q_std.values())
        tp_test = sum(q_test.values())

        n_std = 0
        n_test = 0
        for cluster in clusters:
            if cluster.std == None:
                n_test += 1
                continue
            if not cluster.std.is_ignored:
                n_std += 1
                n_test += len(cluster.test)

        return Metrics.create(tp_std, tp_test, n_std, n_test)

    def describeMatching(self):
        """Returns a string description of the matching this optimizer built"""
        res = '{:4}\t{:4}\t{:4}\t{:8}\n'.format('Res', 'Q_A', 'Q_Id', 'Facts')
        res += '\n'.join([c.toInlineString() for c in self.clusters])
        res += '\n\n'
        res += '-------METRICS------\n'
        res += Metrics.header() + '\n'
        res += self.metrics.toLine()
        return res


#########################################################################################

class Cluster:
    """An evaluation cluster, consists of one standard object and any amount of test
    objects"""

    def __init__(self):
        self.std = None
        self.test = []
        self.arg_quality = -1
        self.id_quality = -1
        self.quality = -1
        
    def add(self, test_obj):
        """Adds another test object to the cluster"""
        
        self.test.append(test_obj)
        
    def calculateQuality(self):
        """Calculate quality"""

        if self.std == None or len(self.test) == 0 or self.std.is_ignored:
            self.arg_quality = 0
            self.id_quality = 0
            self.quality = 0
            return

        # we're dealing with a proper matching
        self._doCalculateQuality()

        self.quality = (self.arg_quality + self.id_quality * self.arg_quality) / 2.0

    def _doCalculateQuality(self):
        """Calculates the matchings argument extraction and identification quality"""
        t_args = []
        for t in self.test:
            t_args.extend(t.arguments)

        matched_t_args = set()
        unmatched_t_args = set(t_args)
        matched_s_args = set()
        unmatched_s_args = set(self.std.arguments)
        t_by_s = dict([(s, []) for s in self.std.arguments])
        s_by_t = dict()
        for t in t_args:
            found_match = False
            for s in self.std.arguments:
                if s.canMatch(t):
                    found_match = True
                    if s in unmatched_s_args:
                        unmatched_s_args.remove(s)
                    unmatched_t_args.remove(t)
                    matched_s_args.add(s)
                    matched_t_args.add(t)
                    t_by_s[s].append(t)
                    s_by_t[t] = s
                    break
            if found_match:
                continue

        n = sum(Tables.getArgumentWeight(x.name) for x in matched_s_args)
        fp = sum(Tables.getArgumentWeight(x.name) for x in unmatched_t_args)
        fn = sum(Tables.getArgumentWeight(x.name) for x in unmatched_s_args)
        self.arg_quality = n / float(n + fp + fn)
        if(self.arg_quality > 1):
            print(self)
        
        denominator = len(matched_s_args) * (len(matched_s_args) - 1) / 2.0
        edges = set()
        for i in range(len(matched_s_args)):
            for j in range(i+1, len(matched_s_args)):
                x = self.std.arguments[i]
                y = self.std.arguments[j]

                for t1 in t_by_s[x]:
                    for t2 in t_by_s[y]:
                        if t1.fact == t2.fact:
                            edges.add((x,y))

        if len(self.test) == 1:
            self.id_quality = 1.0
        else:
            self.id_quality = 1.0 if denominator == 0 else len(edges) / denominator


    def toInlineString(self):
        """Create an inline description of a cluster"""
        if self.std != None and self.std.is_ignored:
            res = '\tIGNORED\t\t'
        else:
            res = '{:.2f}\t{:.2f}\t{:.2f}\t'.format(self.quality, self.arg_quality, self.id_quality)
        res += self.std.toInlineString() if self.std != None else '[---unmatched---]'
        res += '\t=\t'
        if len(self.test) == 0:
            res += '[---unmatched---]'
            return res

        res += ', '.join([x.toInlineString() for x in self.test])
        return res

    @classmethod
    def unpairedTest(cls, test):
        cluster = cls()
        cluster.test.append(test)
        return cluster

    @classmethod
    def unpairedStandard(cls, std):
        cluster = cls()
        cluster.std = std
        return cluster