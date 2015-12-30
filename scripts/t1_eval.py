# Runs the evaluation of the task 1 response

# Usage:
# <Python3 executable> t1_eval.py -s [std_dir] -t [test_dir] -[True/False]

#########################################################################################

import sys
import os
import getopt

from dialent.task1.util import Evaluator

#########################################################################################

def usage():
    print('Usage:')
    print('<Python3 executable> t1_eval.py -s <std_dir> -t <test_dir> [-l]')
    print('    -s [std_dir]    - path to the standard files directory')
    print('    -t [test_dir]   - path to the response files directory')
    print('    -l              - if included, disables "locorg" entity evaluation')
    print('                      (such entities will be considered locations)')
    print('    -h              - display this message')

def main():
    """
        Runs comparison
    """
    try:
        opts, args = getopt.getopt(sys.argv[1:], 's:t:hl')
    except getopt.GetoptError as err:
        print(str(err))
        usage()
        sys.exit(2)

    is_locorg_allowed = True
    std_path = None
    test_path = None
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
        else:
            assert False, 'unhandled option'

    assert std_path != None and test_path != None, 'Stnadard and test paths must be set'\
        '(see python t1_eval.py -h)'

    #from dialent.standard import Standard
    #s = Standard('book_58', 'D:/work/romip/standard')
    #print(s.tokens)

    e = Evaluator()
    e.evaluate(std_path, test_path, is_locorg_allowed)

if __name__ == '__main__':
    main()

