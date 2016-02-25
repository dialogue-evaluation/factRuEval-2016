# Runs the evaluation of the task 1 response
# Requires python 3 and numpy

# Usage:
#
#   <Python3 executable> t1_eval.py -s <std_dir> -t <test_dir> [-l]
#       -s [std_dir]    - path to the standard files directory
#       -t [test_dir]   - path to the response files directory
#       -l              - if included, disables "locorg" mention evaluation
#                         (such mentions will be considered locations)
#       -h              - display this message
#

#########################################################################################

import sys
import os
import getopt

from dialent.task1.eval import Evaluator

#########################################################################################

def usage():
    print('Usage:')
    print('<Python3 executable> t1_eval.py -s <std_dir> -t <test_dir> [-l]')
    print('    -s [std_dir]    - path to the standard files directory')
    print('    -t [test_dir]   - path to the response files directory')
    print('    -o [output_dir] - path to the comparator reports folder')
    print('    -l              - if included, disables "locorg" mention evaluation')
    print('                      (such mentions will be considered locations)')
    print('    -h              - display this message')

def main():
    """
        Runs comparison
    """
    try:
        opts, args = getopt.getopt(sys.argv[1:], 's:t:o:hl')
    except getopt.GetoptError as err:
        print(str(err))
        usage()
        sys.exit(2)

    is_locorg_allowed = True
    std_path = None
    test_path = None
    out_path = ''
    for o, a in opts:
        if o == '-l':
            is_locorg_allowed = False
        elif o == '-h':
            usage()
            sys.exit()
        elif o == '-s':
            std_path = a
        elif o == '-t':
            test_path = a
        elif o == '-o':
            out_path = a
        else:
            assert False, 'unhandled option'

    assert std_path != None and test_path != None, 'Stnadard and test paths must be set'\
        '(see python t1_eval.py -h)'

    e = Evaluator(is_locorg_allowed)
    e.evaluate(std_path, test_path, out_path)

if __name__ == '__main__':
    main()

