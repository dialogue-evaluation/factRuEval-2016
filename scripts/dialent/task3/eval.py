# This module contains task 3 evaluation logic

import os

from dialent.config import Tables

from dialent.standard import Standard
from dialent.task3.test import Test

from dialent.objects.fact import Fact
from dialent.common.metrics import Metrics

from dialent.task3.util import loadAllStandard
from dialent.task3.util import loadAllTest

from time import localtime, strftime

#########################################################################################

class Evaluator:
    """Evaluates the task 3 responses"""

    # Tags used in statistics (everything but the ignored 'IsPartOf')
    stat_tags = ['ownership', 'occupation', 'meeting', 'deal', 'overall']

    def __init__(self, hard_mode=False):
        self.hard_mode = hard_mode

    def evaluate(self, std_path, test_path, output_path, is_silent=False):
        if not is_silent:
            print('Running evaluation, this might take a while...')
        std = loadAllStandard(std_path)
        test = loadAllTest(test_path)
        
        diff = set([x.name for x in std]).symmetric_difference(
            set([y.name for y in test]))

        assert(len(diff) == 0)
        res = dict((x, Metrics()) for x in Evaluator.stat_tags)

        for i, s in enumerate(std):
            if not s.has_facts:
                # do not compare documents without a .facts file
                # this is just for convenience
                continue
            metrics = self.evaluateDocument(s, test[i])
            self.printReport(s.name, output_path)
            for tag in Evaluator.stat_tags:
                res[tag].add(metrics[tag])
            
        if not is_silent:
            print('TAG             ' + Metrics.header())
            for tag in Evaluator.stat_tags:
                print('{:15} '.format(tag) + res[tag].toLine())

        return res

    def evaluateDocument(self, std, test):
        self.metrics = dict((x, Metrics()) for x in Evaluator.stat_tags)
        self.clusters = []
        for tag in Evaluator.stat_tags:
            if tag == 'overall':
                continue
            tag_std = [s for s in std.facts if s.tag == tag]
            tag_test = [t for t in test.facts if t.tag == tag]
            self.optimizer = Optimizer(tag_std, tag_test, self.hard_mode)
            self.optimizer.findSolution()
            
            self.metrics[tag].add(self.optimizer.metrics)
            self.metrics['overall'].add(self.optimizer.metrics)
            self.clusters.extend(self.optimizer.clusters)
        
        return self.metrics

    def buildReport(self):
        """Build an evaluation report"""
        return self.optimizer.describeMatching(self.clusters, self.metrics)

    def printReport(self, name, out_dir):
        """Print a detailed report on the document evaluation"""
        if len(out_dir) == 0:
            return

        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, name + '.report.txt'), 'w', encoding='utf-8') as f:
            f.write(self.buildReport())

class Optimizer:
    """Optimizes the matching"""

    def __init__(self, std, test, hard_mode):
        self.test = test
        self.hard_mode = hard_mode

        if hard_mode:
            # hard mode, remove all facts with modality other than 'actual'
            self.std = [x for x in std if not x.has_easymode_modality]
        else:
            # easy mode, ignore all facts marked as difficult, and remove phase argument
            self.std = std
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

    def describeMatching(self, clusters, metrics):
        """Returns a string description of the matching this optimizer built"""
        res = ''
        for i, c in enumerate(clusters):
            res += '---- #{} ----\n'.format(i+1)
            res += c.toInlineString() + '\n'
        res += '\n\n'
        res += '-------METRICS------\n'
        res += 'TAG             ' + Metrics.header() + '\n'
        for tag in Evaluator.stat_tags:
            res += '{:15} '.format(tag) + metrics[tag].toLine() + '\n'
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
        self._doCalculateQuality()
        self.quality = (self.arg_quality + self.id_quality * self.arg_quality) / 2.0

    def _doCalculateQuality(self):
        """Calculates the matchings argument extraction and identification quality"""
        t_args = []
        for t in self.test:
            t_args.extend(t.arguments)

        s_args = self.std.arguments if self.std != None else []

        matched_t_args = set()
        self.unmatched_t_args = set(t_args)
        matched_s_args = set()
        self.unmatched_s_args = set(s_args)
        self.t_by_s = dict([(s, []) for s in s_args])
        self.s_by_t = dict()
        
        if self.std == None or len(self.test) == 0 or self.std.is_ignored:
            # matching with objects on one side
            self.arg_quality = 0
            self.id_quality = 0
            self.quality = 0
            return

        for t in t_args:
            found_match = False
            for s in self.std.arguments:
                if s.canMatch(t):
                    found_match = True
                    if s in self.unmatched_s_args:
                        self.unmatched_s_args.remove(s)
                    self.unmatched_t_args.remove(t)
                    matched_s_args.add(s)
                    matched_t_args.add(t)
                    self.t_by_s[s].append(t)
                    self.s_by_t[t] = s
                    break
            if found_match:
                continue

        n = sum(Tables.getArgumentWeight(x.name) for x in matched_s_args)
        fp = sum(Tables.getArgumentWeight(x.name) for x in self.unmatched_t_args)
        fn = sum(Tables.getArgumentWeight(x.name) for x in self.unmatched_s_args)
        self.arg_quality = n / float(n + fp + fn)
        if(self.arg_quality > 1):
            print(self)
        
        denominator = len(matched_s_args) * (len(matched_s_args) - 1) / 2.0
        edges = set()
        for i in range(len(matched_s_args)):
            for j in range(i+1, len(matched_s_args)):
                x = self.std.arguments[i]
                y = self.std.arguments[j]

                for t1 in self.t_by_s[x]:
                    for t2 in self.t_by_s[y]:
                        if t1.fact == t2.fact:
                            edges.add((x,y))

        if len(self.test) == 1:
            self.id_quality = 1.0
        else:
            self.id_quality = 1.0 if denominator == 0 else len(edges) / denominator


    def toInlineString(self):
        """Create an inline description of a cluster"""
        if self.std != None and self.std.is_ignored:
            res = 'Quality:\n\t(IGNORED)\n\n'
        else:
            res = 'Quality:\n'
            res += '\tArgument extraction quality = {:.2f}\n'.format(self.arg_quality)
            res += '\tIdentification quality = {:.2f}\n'.format(self.id_quality)
            res += '\tOVERALL = {:.2f}\n'.format(self.quality)
            res += '\n'

        res += 'STANDARD:\n\t' + (
            self.std.toInlineString() if self.std != None else '[---unmatched---]')
        
        res += '\nTEST:\n\t'
        if len(self.test) == 0:
            res += '[---unmatched---]\n\n'
            return res

        res += ', '.join([x.toInlineString() for x in self.test]) + '\n'

        if self.std == None:
            return res

        res += '\nARGUMENTS:\n'
        for arg in self.t_by_s:
            if len(self.t_by_s[arg]) == 0:
                assert(arg in self.unmatched_s_args)
                continue

            res += ('\t{} = {}\n'.format(
                str(arg),
                ', '.join(str(t) for t in self.t_by_s[arg])))

        for arg in self.unmatched_s_args:
            res += '\t{} = {}\n'.format(arg, '[---unmatched---]')

        for arg in self.unmatched_t_args:
            res += '\t{} = {}\n'.format('[---unmatched---]', arg)

        return res

    def __str__(self):
        return 'Cluster:\nS={}\nT={}\n'.format(self.std, self.test)

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