  Evaluation scripts:

This folder contains FactRuEval-2016 evaluation scripts.

To run the scripts you'll need a python 3 distribution, and, in some cases,
some additional packages (see below).

Please make sure that your submission files are in utf-8 without BOM, are located
in a separate folder. The submission should have a .trackX file for every set of
'book_YY' documents. Empty files are accepted by the evaluation script, but extra
or missing files will result in warnings

All of the follwing scripts require python 3 and numpy

---------------------

  t1_eval.py:

Runs the evaluation of the task 1 response

Usage:

    <Python3 executable> t1_eval.py -s <std_dir> -t <test_dir> [-l]
        -s [std_dir]    - path to the standard files directory
        -t [test_dir]   - path to the response files directory
		-o [output_dir] - path to the comparator reports folder
        -l              - if included, disables "locorg" entity evaluation
                          (such entities will be considered locations)
        -h              - display usage

---------------------
		
	t2_eval.py
	
Runs the evaluation of the task 2 response

Usage:

	<Python3 executable> t2_eval.py -s <std_dir> -t <test_dir> [-o <output_dir>] [-m]
		-s [std_dir]    - path to the standard files directory
		-t [test_dir]   - path to the response files directory
		-o [output_dir] - path to the comparator reports folder
		-m              - enables the simplified comparison mode (no penalty for extra values)
        -h              - display usage

---------------------
		
	t3_eval.py
	
Runs the evaluation of the task 3 response

Usage:

	<Python3 executable> t3_eval.py -s <std_dir> -t <test_dir> [-o <output_dir>] [-m]
		-s [std_dir]    - path to the standard files directory
		-t [test_dir]   - path to the response files directory
		-o [output_dir] - path to the comparator reports folder
		-m              - enable hard mode
        -h              - display usage
