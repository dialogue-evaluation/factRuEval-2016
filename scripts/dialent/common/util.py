# This module contains various functions used throughout all the tasks

#########################################################################################

def safeOpen(filename):
    """Open a utf-8 file with or without BOM in read mode"""
    for enc in ['utf-8-sig', 'utf-8']:
        try:
            f = open(filename, 'r', encoding=enc)
        except Exception as e:
            print(e)
            f = None

        if f != None:
            return f
