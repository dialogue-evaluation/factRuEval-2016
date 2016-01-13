  Evaluation scripts:

This folder contains FactRuEval-2016 evaluation scripts.
Currently the only available script is the one for the first track.

To run the scripts you'll need a python 3 distribution, and, in some cases,
some additional packages (see below).

Please make sure that your submission files are in utf-8 without BOM, are located
in a separate folder. The submission should have a .trackX file for every set of
'book_YY' documents. Empty files are accepted by the evaluation script, but extra
or missing files will result in warnings


  t1_eval.py:

Runs the evaluation of the task 1 response
Requires python 3 and numpy

Usage:

    <Python3 executable> t1_eval.py -s <std_dir> -t <test_dir> [-l]
        -s [std_dir]    - path to the standard files directory
        -t [test_dir]   - path to the response files directory
        -l              - if included, disables "locorg" entity evaluation
                          (such entities will be considered locations)
        -h              - display this message

