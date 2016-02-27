# This module deals with test data representation for the second task

#########################################################################################

import os
import csv

from dialent.common.util import safeOpen
from dialent.common.util import normalize

from dialent.config import Config

from dialent.objects.entity import Entity

from dialent.standard import Standard

#########################################################################################

class Test:
    """Task2 test markup with several entities"""

    def __init__(self, name, dir='.'):
        """Load the data from the given document
        
        name - file to load the data from (without an extension)
        """
        try:
            self.name = name
            full_name = os.path.join(dir, name + '.task2')
            self.load(full_name)
        except Exception as e:
            print('Failed to load "{}"'.format(full_name))
            print(e)
    

    def load(self, filename):
        """Do the exception-prone loading"""
        self.entities = []

        with safeOpen(filename) as f:
            buffer = ''
            for raw_line in f:
                line = normalize(raw_line)
                if len(line) == 0:
                    if len(buffer) > 0:
                        self.entities.append(Entity.fromTest(buffer))
                        buffer = ''
                else:
                    buffer += line + '\n'
            if len(buffer) > 0:
                self.entities.append(Entity.fromTest(buffer))
                    
                    