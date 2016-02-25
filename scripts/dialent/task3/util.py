# This module has various utility class and methods for the 3rd task

import os

from dialent.task2.util import loadAllStandard
from dialent.task3.test import Test

from dialent.objects.argument import StringValue

#########################################################################################

class ResponseGenerator:
    """Generates a system response for the 3rd track based on the standard markup"""

    def generate(self, standard_path, test_path):
        """Loads the stnadard markup from standard_path, generates a response and saves 
        it to the test_path"""

        os.makedirs(test_path, exist_ok = True)

        std = loadAllStandard(standard_path)
        for s in std:
            self.generateDoc(s, os.path.join(test_path, s.name + '.task3'))

    def generateDoc(self, std, filename):
        """Generates a test markup for the given standard markup and saves it to
        filename"""

        print('Processing {}'.format(std.name))
        res = ''

        for fact in std.facts:
            res += fact.toTestString() + '\n'

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(res)

#########################################################################################
# various utility methods

def loadAllTest(path):
    """Load all test files from test_path. Returns a list of dialent.task3.test.Test
    objects"""
    
    names = set(x.split('.')[0] for x in os.listdir(path) if '.task3' in x)
    res = [Test(name, path) for name in names]
    
    return sorted(res, key=lambda x: int(x.name[5:]))   # book_XXX - sort by number


def validate(standard_path):
    """Prints various information on standard files in the given directory"""
    std = loadAllStandard(standard_path)

    no_fact_count = 0
    f_attr_count = dict()
    f_attr_value_count = dict()

    for s in std:
        if not s.has_facts:
            no_fact_count += 1
        for f in s.facts:
            for a in f.arguments:
                key = f.tag + ' - ' + a.name
                if key in f_attr_count:
                    f_attr_count[key] += 1
                else:
                    f_attr_count[key] = 1

                for val in a.values:
                    if not isinstance(val, StringValue):
                        if 'span' in val.values:
                            print('SPAN IN VAL!!!!')

                if a.name in ['модальность', 'сложность', 'фаза']:
                    key = f.tag + ' - ' + a.name + ' - ' + a.values[0].descr
                    if key in f_attr_value_count:
                        f_attr_value_count[key] += 1
                    else:
                        f_attr_value_count[key] = 1
                    

    print('Fact standard statistics for "{}":'.format(standard_path))
    print('Total files: {}'.format(len(std)))
    print('Files with no fact layer: {}'.format(no_fact_count))
    print('Fact-argument pair counts:')
    for key in sorted(f_attr_count.keys()):
        print('    {}\t{}'.format(key, f_attr_count[key]))
    print('Fact-argument-value counts for the auxiliary arguments:')
    for key in sorted(f_attr_value_count.keys()):
        print('    {}\t{}'.format(key, f_attr_value_count[key]))
