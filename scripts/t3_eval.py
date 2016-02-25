# Runs the evaluation of the task 3 response
# Requires python 3 and numpy

# Usage:
#
#   <Python3 executable> t3_eval.py -s <std_dir> -t <test_dir> [-o <output_dir>] [-m]
#       -s [std_dir]    - path to the standard files directory
#       -t [test_dir]   - path to the response files directory
#       -o [output_dir] - path to the comparator reports folder
#       -m              - enable hard mode
#       -h              - display this message
#

#########################################################################################

import sys
import os
import getopt

from dialent.task3.eval import Evaluator

#########################################################################################

def usage():
    print('Usage:')
    print('<Python3 executable> t3_eval.py -s <std_dir> -t <test_dir> [-o <output_dir>] [-m]')
    print('    -s [std_dir]    - path to the standard files directory')
    print('    -t [test_dir]   - path to the response files directory')
    print('    -o [output_dir] - path to the comparator reports folder')
    print('    -m              - enable hard mode')
    print('    -h              - display this message')

def main():
    """
        Runs comparison
    """
    try:
        opts, args = getopt.getopt(sys.argv[1:], 's:t:o:hm')
    except getopt.GetoptError as err:
        print(str(err))
        usage()
        sys.exit(2)

    std_path = None
    test_path = None
    out_path = ''
    hard_mode = False
    for o, a in opts:
        if o == '-h':
            usage()
            sys.exit()
        elif o == '-s':
            std_path = a
        elif o == '-t':
            test_path = a
        elif o == '-o':
            out_path = a
        elif o == '-m':
            hard_mode = True
        else:
            assert False, 'unhandled option'

    assert std_path != None and test_path != None, 'Stnadard and test paths must be set'\
        '(see python t3_eval.py -h)'

    e = Evaluator(hard_mode)
    e.evaluate(std_path, test_path, out_path)

if __name__ == '__main__':
    main()

