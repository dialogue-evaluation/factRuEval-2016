# This module deals with test data representation for the third task

#########################################################################################

import os

from dialent.common.util import normalize
from dialent.common.util import safeOpen

from dialent.objects.fact import Fact

#########################################################################################

class Test:
    """Test markup for the third track"""

    def __init__(self, name, dir='.'):
        """Load the data from the given document
        
        name - file to load the data from (without an extension)
        """
        try:
            self.name = name
            full_name = os.path.join(dir, name + '.task3')
            self.load(full_name)
        except Exception as e:
            print('Failed to load "{}"'.format(full_name))
            print(e)
    

    def load(self, filename):
        """Do the exception-prone loading"""
        self.facts = []

        with safeOpen(filename) as f:
            buffer = ''
            for raw_line in f:
                line = normalize(raw_line)
                if len(line) == 0:
                    if len(buffer) > 0:
                        self.facts.append(Fact.fromTest(buffer))
                        buffer = ''
                else:
                    buffer += line + '\n'
            if len(buffer) > 0:
                self.facts.append(Fact.fromTest(buffer))
                    
