# Validates the submission for a task
# Requires python 3 and numpy

# Usage:
#
#   <Python3 executable> validate.py [dir]
#       [dir]    - path to the submission files directory
#       Submission track is detected by file extension

import os
import sys

from dialent.task1.util import loadAllTest as loadTask1
from dialent.task2.util import loadAllTest as loadTask2
from dialent.task3.util import loadAllTest as loadTask3

def validate(directory):
    """Runs validation of the task submission in the given directory"""
    
    ext = set([x.split('.')[-1] for x in os.listdir(directory)])

    func_by_task = {
        '1' : loadTask1,
        '2' : loadTask2,
        '3' : loadTask3
    }

    print('Validating directory: {} ...'.format(directory))
    for task in ['1', '2', '3']:
        if 'task' + task in ext:
            t = func_by_task[task](directory)
            print(' ... Loaded {} submission files for task {}'.format(
                len(t), task))


def showUsage():
    print('This script validates the submission for a task')
    print('It does nothing other than attempting to load test files')
    print('The task is detected automatically by the file extension')
    print('')
    print(' Usage:')
    print('')
    print('   <Python3 executable> validate.py [dir]')
    print('      [dir]    - path to the submission files directory')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        showUsage()
    else:
        validate(sys.argv[1])