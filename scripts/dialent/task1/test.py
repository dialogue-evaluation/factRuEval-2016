# This module deals with test data representation for the first task

#########################################################################################

import os
import csv

from dialent.config import Config

from dialent.objects import Interval
from dialent.objects import Token
from dialent.objects import TokenSet

from dialent.standard import Standard

#########################################################################################

class Test:
    """Test data for the first track"""
    
    def __init__(self, name, dir='.'):
        """Load the data from the given document
        
        name - file to load the data from (without an extension)
        """
        try:
            full_name = os.path.join(dir, name + '.task1')
            self.load(full_name)
        except Exception as e:
            print('Failed to load "{}"'.format(full_name))
            print(e)
    

    def load(self, filename):
        """Do the exception-prone loading"""
        
        # set the allowed tags for later
        self.allowed_tags = set(['org', 'per', 'loc', 'locorg'])
            
        self.entities = {}
        for tag in self.allowed_tags:
            self.entities[tag] = []
            
        # read the file that should consist of lines like
        # [TAG] [START_SYMBOL_INDEX] [LENGTH]
        with open(filename, 'r') as f:
            r = csv.reader(f, delimiter=' ', quotechar=Config.QUOTECHAR)
            for index, parts in enumerate(r):
                # skip the empty lines
                if len(parts) == 0:
                    continue
                    
                try:
                    assert(len(parts) == 3)
                    tag = parts[0].lower()
                    assert(tag in self.allowed_tags)
                    self.entities[tag].append(Interval(*parts[1:]))
                except Exception as e:
                    line_descr = '[{}] [START_SYMBOL_INDEX] [LENGTH]'.format(
                                '/'.join(self.allowed_tags))
                    raise Exception(
                        'Error: "{}", line {}.\nExpected: {}\nReceived: {}\nDetails: {}'.format(
                            filename, index, line_descr, ' '.join(parts), str(e)))
                    
                    
    def makeTokenSets(self, standard, is_locorg_allowed=True):
        """Create a dictionary of typed TokenSet objects corresponding to the entities,
        using the provided standard data to tokenize the intervals"""
        
        res = dict([(x, []) for x in self.allowed_tags])
        for key in self.allowed_tags:
            for interval in self.entities[key]:
                ts = TokenSet([token
                              for token in standard.tokens
                                  if token.start >= interval.start
                                      and token.end <= interval.end
                                      and not token.isIgnored()],
                             key)
                if not is_locorg_allowed and key == 'locorg':
                    ts.tag = 'loc'
                res[ts.tag].append(ts)
        
        if not is_locorg_allowed:
            assert(len(res['locorg']) == 0)
            res.pop('locorg')
        return res