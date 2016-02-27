# This module deals with test data representation for the first task

#########################################################################################

import os
import csv

from dialent.common.util import safeOpen
from dialent.common.util import normalize

from dialent.config import Config

from dialent.objects.interval import Interval
from dialent.objects.token import Token
from dialent.objects.tokenset import TokenSet

from dialent.standard import Standard

#########################################################################################

class Test:
    """Test data for the first track"""
    
    def __init__(self, name, dir='.'):
        """Load the data from the given document
        
        name - file to load the data from (without an extension)
        """
        try:
            self.name = name
            full_name = os.path.join(dir, name + '.task1')
            self.load(full_name)
        except Exception as e:
            print('Failed to load "{}"'.format(full_name))
            print(e)
    

    def load(self, filename):
        """Do the exception-prone loading"""
        
        # set the allowed tags for later
        self.allowed_tags = set(['org', 'per', 'loc', 'locorg'])
            
        self.mentions = {}
        for tag in self.allowed_tags:
            self.mentions[tag] = []
            
        # read the file that should consist of lines like
        # [TAG] [START_SYMBOL_INDEX] [LENGTH]
        with safeOpen(filename) as f:
            r = csv.reader(f, delimiter=' ', quotechar=Config.QUOTECHAR)
            for index, parts in enumerate(r):
                # skip the empty lines
                if len(parts) == 0:
                    continue
                    
                try:
                    assert(len(parts) == 3)
                    tag = normalize(parts[0])
                    assert(tag in self.allowed_tags)
                    self.mentions[tag].append(Interval(*parts[1:]))
                except Exception as e:
                    line_descr = '[{}] [START_SYMBOL_INDEX] [LENGTH]'.format(
                                '/'.join(self.allowed_tags))
                    raise Exception(
                        'Error: "{}", line {}.\nExpected: {}\nReceived: {}\nDetails: {}'.format(
                            filename, index, line_descr, ' '.join(parts), str(e)))
                    
                    
    def makeTokenSets(self, standard, is_locorg_allowed=True):
        """Create a dictionary of typed TokenSet objects corresponding to the mentions,
        using the provided standard data to tokenize the intervals"""
        
        res = []
        for key in self.allowed_tags:
            for interval in self.mentions[key]:
                ts = TokenSet([token
                              for token in standard.tokens
                                  if token.start >= interval.start
                                      and token.end <= interval.end
                                      and not token.isIgnored()],
                             key, standard.text)

                # save the interval within the token set
                # to display it as-is in future
                ts.interval = interval

                if not is_locorg_allowed and key == 'locorg':
                    ts.tag = 'loc'
                res.append(ts)
        
        return res