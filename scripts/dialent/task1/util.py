# This module contains two utilities for the first track:
#   - evaluator
#   - automatic response generator

#########################################################################################

import os
import numpy as np

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
            std = Standard(name)
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
            res += self._doBuildResponse(tag, s[tag])
        
        os.makedirs(os.path.dirname(out_filename), exist_ok=True)
        with open(out_filename, 'w') as f:
            f.write(res)
        
                
    def _doBuildResponse(self, tag, token_sets):
        """
            Build a partial response assotiated with the given tag

            tag - entity type tag
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
            is_locorg_allowed - enables/disables 'locorg' entity type
        """

        res,tmp = self._doEvaluate(std_dir, test_dir, is_locorg_allowed)
        print(summary_header_template.format(
            'Type', 'P', 'R', 'F1', 'TP', 'In Std.', 'In Test.'))

        tp = 0
        n_std = 0
        n_test = 0

        for key in res:
            print(summary_line_template.format(key, *res[key]))
            tp += res[key][3]
            n_std += res[key][4]
            n_test += res[key][5]

        overall = self._calcMetrics(tp, n_std, n_test)
        print('')
        print(summary_line_template.format('Overall', *overall))
        

    def resultByDocument(self, std_dir, test_dir, is_locorg_allowed=True):
        """
            Run the evaluation of the provided response, and print the result for every
            document.

            std_dir - standard markup files directory
            test_dir - responese directory
            is_locorg_allowed - enables/disables 'locorg' entity type
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

            Returns a dictionary of metrics by entity type.
            Metrics include precision, recall, f1,
            true positive count, standard size and test size
            in that order.

            std_dir - standard markup files directory
            test_dir - response files directory
            is_locorg_allowed - enables/disables 'locorg' entity type
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
        return dict([(tag, self._calcMetrics(tp[tag], n_std[tag], n_test[tag]))
                   for tag in allowed_tags]), doc_results
    

    def evaluateDocument(self, standard, test, is_locorg_allowed=True):
        """
            Compare the provided standard and test markup.

            Returns a dictionary of metrics by entity type.
            Metrics include precision, recall, f1,
            true positive count, standard size and test size
            in that order.

            standard - loaded standard document
            test - loaded test document
            is_locorg_allowed - enables/disables 'locorg' entity type
        """
        s = standard.makeTokenSets(is_locorg_allowed)
        t = test.makeTokenSets(standard, is_locorg_allowed)

        allowed_tags = ['per', 'org', 'loc']
        if is_locorg_allowed:
            allowed_tags.append('locorg')

        return dict([(x, self.doCompareTag(s[x], t[x])) for x in allowed_tags])


    def _recursiveSearch(self, m, std, test, weight, pairs):
        """
            Run a recursive search of the maximum matching.

            Returns the following tuple:
                (best weight, list of pairs that achieve the best weight)

            m - cost matrix
            std - standard indices list
            test - test indices list
            weight - current accumulated weight
            pairs - current list of built pairs
        """
        if len(std) == 0 or len(test) == 0:
            return weight, pairs

        curr = std[0]
        max_res = (weight, pairs)

        possible_pairs_count = 0
        pair_max_alternatives = 0
        for i, t in enumerate(test):
            if m[curr, t] != 0:

                # first gather information on possible actions
                possible_pairs_count += 1
                alt_count = 0
                for k in std:
                    if m[k, t] != 0:
                        alt_count += 1
                    if alt_count > pair_max_alternatives:
                        pair_max_alternatives = alt_count
                
                # try to confirm the pair
                res = self._recursiveSearch(
                    m, std[1:], test[:i] + test[i+1:],
                    weight + m[curr, t],
                    pairs + [(curr, t)])
                if res[0] > max_res[0]:
                    max_res = res

        # check what would happen if this standard object were ignored
        # this check is obviously performance-heavy and only necessary under
        # these conditions
        if (possible_pairs_count == 0 or
                possible_pairs_count == 1 and pair_max_alternatives > 1):
            res = self._recursiveSearch(
                m, std[1:], test,
                weight,
                pairs)
            if res[0] > max_res[0]:
                max_res = res

        return max_res
    

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

        n_std = len(std)
        n_test = len(test)
        m = np.zeros((n_std, n_test))

        # fill the bipartite graph cost matrix
        for i, s in enumerate(std):
            for j, t in enumerate(test):
                if s.intersects(t):
                    m[i, j] = self._calculatePairPriority(std[i], test[j])

        # find the maximum matching
        # uses naive search due to matrix sparcity,
        # as well as scipy 0.17 being unavailable :(

        s_ind = list(range(n_std))
        t_ind = list(range(n_test))

        # find the matching and calculate metrics
        priority, pairs = self._recursiveSearch(m, s_ind, t_ind, 0, [])
        tp = 0
        for i, j in pairs:
            tp += self._calculatePairQuality(std[i], test[j])
        return self._calcMetrics(tp, n_std, n_test)
    
    # utility methods
    
    def _calculatePairPriority(self, s, t):
        """Calculate the preliminary quality of a matched pair"""
        return self._doEvalPair(s, t, Tables.PRIORITY)
    

    def _calculatePairQuality(self, s, t):
        """Calculate the final quality of a matched pair"""
        return self._doEvalPair(s, t, Tables.QUALITY)
    

    def _doEvalPair(self, s, t, ref_table):
        """Evaluate pair using the provided reference table"""

        tokens_tp = s.tokens.intersection(t.tokens)
        tokens_fn = s.tokens.difference(t.tokens)
        
        tp = 0.0
        for token in tokens_tp:
            tp += ref_table[s.tag][s.mark(token)]

        fn = 0.0
        for token in tokens_fn:
            fn += ref_table[s.tag][s.mark(token)]

                
        fp = len(t.tokens.difference(s.tokens))
        
        summ = tp + fp + fn
        assert(summ > 0)
        return tp / summ
    

    def _calcMetrics(self, tp, n_std, n_test):
        """Calculate precision, recall and f1"""

        # default precision and recall are set to 1
        # because technically an empty test corresponding to an empty standard
        # should be the correct answer
        precision = (tp / float(n_test)) if n_test > 0 else 1
        recall = (tp / float(n_std)) if n_std > 0 else 1
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        return (precision, recall, f1, tp, n_std, n_test)

