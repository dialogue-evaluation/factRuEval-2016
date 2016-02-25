# Runs the evaluation of the task 2 response
# Requires python 3 and numpy

# Usage:
#
#   <Python3 executable> t2_eval.py -s <std_dir> -t <test_dir> [-o <output_dir>] [-m]
#       -s [std_dir]    - path to the standard files directory
#       -t [test_dir]   - path to the response files directory
#       -o [output_dir] - path to the comparator reports folder
#       -m              - enables the simplified comparison mode (no penalty for extra values)
#       -h              - display this message
#

#########################################################################################

import sys
import os
import getopt

from dialent.task2.eval import Evaluator

#########################################################################################

def usage():
    print('Usage:')
    print('<Python3 executable> t2_eval.py -s <std_dir> -t <test_dir> [-o <output_dir>] [-m]')
    print('    -s [std_dir]    - path to the standard files directory')
    print('    -t [test_dir]   - path to the response files directory')
    print('    -o [output_dir] - path to the comparator reports folder')
    print('    -m              - enables the simplified comparison mode (no penalty for extra values)')
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
    mode = 'regular'
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
            mode = 'simple'
        else:
            assert False, 'unhandled option'

    assert std_path != None and test_path != None, 'Stnadard and test paths must be set'\
        '(see python t2_eval.py -h)'

    e = Evaluator(mode)
    e.evaluate(std_path, test_path, out_path)

if __name__ == '__main__':
    main()

