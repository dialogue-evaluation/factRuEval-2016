# This module contains evaluators own functionality testing logic

import os

from dialent.standard import Standard

from dialent.task1.test import Test as Test1
from dialent.task1.eval import Evaluator as Eval1

from dialent.task2.test import Test as Test2
from dialent.task2.eval import Evaluator as Eval2

from dialent.task3.test import Test as Test3
from dialent.task3.eval import Evaluator as Eval3

#########################################################################################

eps = 0.01

def createEvaluator(task, mode):
    """Create an evaluator corresponding to the given task/mode combination"""
    if task == 1 and mode == '-':
        return Eval1()
    elif task == 1 and mode == 'l':
        return Eval1(False)
    elif task == 2 and mode == '-':
        return Eval2('regular')
    elif task == 2 and mode == 'm':
        return Eval2('simple')
    elif task == 3 and mode == '-':
        return Eval3()
    elif task == 3 and mode == 'm':
        return Eval3(True)
    else:
        print('Unacceptable task/mode combination : {}/{}'.format(task, mode))
        return None

def loadTest(task, name, dir):
    """Create a test markup for the given task"""
    if task == 1:
        return Test1(name, dir)
    elif task == 2:
        return Test2(name, dir)
    elif task == 3:
        return Test3(name, dir)
    else:
        print('Unacceptable task: {}'.format(task))
        return None

#########################################################################################

class TestManager:
    """This class is designed to validate evaluator funcionality for all the tracks.
    It loads a test instruction file and runs the tests"""

    def __init__(self):
        """Create a new test manager"""
        self.test_filename = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'dialent/tests/test_list.txt'
            )
        self.path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'dialent/tests'
            )
        self.output_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'dialent/tests/__out'
            )

        os.makedirs(self.output_path, exist_ok=True)
        self.loadTests()

    def loadTests(self):
        """Load the test instruction file"""
        self.tests = []
        with open(self.test_filename, encoding='utf-8') as f:
            for line in f:
                meaningful = line.split('#')[0].strip(' \n\r\t')
                if len(meaningful) == 0:
                    continue

                self.tests.append(FuncTest(meaningful, self))

    def runTest(self, name):
        """Run test or tests with the given name"""
        tests = [x for x in self.tests if name == x.name]
        for test in tests:
            test.run()

    def runAllTests(self):
        """Run all the loaded tests"""
        for test in self.tests:
            self.runTest(test.name)

        failed_tests = [x.name + ' - ' + x.comment for x in self.tests if not x.is_ok]
        if len(failed_tests) > 0:
            print('Failed tests:\n{}'.format('\n'.join(failed_tests)))
            return False
        else:
            return True

#########################################################################################

class FuncTest:
    """Evaluator functionality test"""

    def __init__(self, line, owner):
        """Create a new test using a line in the description file"""

        parts = [x for x in line.split(' ') if len(x) > 0]
        self.task = int(parts[0])
        self.mode = parts[1]
        self.name = parts[2]
        self.correct_f1 = float(parts[3])
        self.comment = ' '.join(parts[4:]) if len(parts) > 4 else ''

        self.owner = owner
        self.metrics = None
        self.is_ok = None

    def run(self):
        """Run a loaded test"""
        print('Running test {:30} '.format(self.name), end='', flush=True)

        eval = createEvaluator(self.task, self.mode)
        self.metrics = eval.evaluate(self.owner.path + '/' + self.name,
                      self.owner.path + '/' + self.name,
                      self.owner.output_path + '/' + self.name,
                      is_silent=True)

        self.is_ok = abs(self.metrics['overall'].f1 - self.correct_f1) < eps
        self.report = eval.buildReport()
        self.report = 'TEST : {}\n===========================\n'.format(
           'SUCCESS' if self.is_ok else 'FAIL!') + self.report

        print('SUCCESS' if self.is_ok else 'FAIL!')

    def __repr__(self):
        return "Task {} (mode '{}') - {} - {:.2f} --- STATUS: {}".format(
            self.task, self.mode,
            self.name, self.correct_f1,
            'N/A' if self.is_ok == None else ('SUCCESS' if self.is_ok else 'FAIL!')
            )

#########################################################################################

if __name__ == '__main__':
    tm = TestManager()
    tm.runAllTests()
