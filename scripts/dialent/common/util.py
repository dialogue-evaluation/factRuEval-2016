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

def safeNormalize(string):
    """Run a number of normalization operations on the given string.
    The string is normalized not in the linguistic sense, but rather in such a way that
    captialization, e/ё and quote simbols become irrelevant in comparison
    
    All unique non-letter chars:  !"$%()*+,-./0123456789:;<=>?«»–—’“”„•…№
    """

    # force lower case
    res = string.lower()

    # trim the string
    res =  res.strip(' \r\n\t')

    # unify all quote symbols
    for s in '«»“”„':
        res = res.replace(s, '"')

    # unify all single quotes
    for s in '’`':
        res = res.replace(s, "'")

    # unify all ё/е
    res = res.replace('ё', 'е')

    # unify all dashes
    for s in '-‐−‒–—―':
        res = res.replace(s, '-')

    return res

def normalize(string):
    """Run a number of normalization operations on the given string.
    The string is normalized not in the linguistic sense, but rather in such a way that
    captialization, e/ё and quote simbols become irrelevant in comparison
    
    Unlike safeNormalize, this function also attempts to get rid of extra spaces before
    punctuation"""

    res = safeNormalize(string)

    # in standard strings are generated from tokens, and sometimes have 1 extra space
    # before or after puntuation symbols

    res = res.replace(' ,', ',')
    res = res.replace(' .', '.')
    res = res.replace(' -', '-')
    res = res.replace('- ', '-')

    res = res.replace('( ', '(')
    res = res.replace(' )', ')')

    return res

class DistCache:
    """Cache for Levenstein distance calculations"""
    table = {

        }

    # rather arbitrary threshold function
    thresholds = [0, 0, 1, 1, 1, 1, 1, 1, 1, 2] # 2 for longer strings

    @classmethod
    def getThreshold(cls, str_len):
        """Return fuzzy comparison threshold for a string of the given length"""
        if str_len >= len(cls.thresholds):
            return cls.thresholds[-1]
        return cls.thresholds[str_len]


def dist(s1, s2):
    """Calculate Levenstein distance between the 2 strings"""
    if len(s2) > len(s1):
        return dist(s2, s1)

    if (s1, s2) in DistCache.table:
        return DistCache.table[(s1, s2)]

    # s1 is of greater or equal length to s2
    if len(s2) == 0:
        return len(s1)

    width = len(s2) + 1
    prev_row = [i for i in range(width)]
    for i, c1 in enumerate(s1):
        cur_row = [i+1] + [0]*(width-1)
        for j, c2 in enumerate(s2):
            cur_row[j+1] = min(
                cur_row[j] + 1,
                prev_row[j+1] + 1,
                prev_row[j] + (1 if c1 != c2 else 0)
            )
        prev_row = cur_row

    DistCache.table[(s1, s2)] = cur_row[-1]

    return cur_row[-1]

def compareStrings(s1, s2):
    """Check if the Levenstein distance between s1 and s2 is less or equal than
    the threshold value. If it is, the strings are considered equal, otherwise not equal"""

    threshold = DistCache.getThreshold(max(len(s1), len(s2)))
    return dist(s1, s2) <= threshold