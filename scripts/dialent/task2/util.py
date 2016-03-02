# This module contains the response generator for the second task
# And some other utility functions/classes

import os

import re

from dialent.standard import Standard
from dialent.task2.test import Test

#########################################################################################

class ResponseGenerator:
    """Generates a response for the track based on the standard"""

    def createResponse(self, std_path, test_path):
        os.makedirs(test_path, exist_ok=True)
        names = set([x.split('.')[0] for x in os.listdir(std_path)])
        for name in names:
            s = Standard(name, std_path)
            self.createDocumentResponse(s, test_path)

    def createDocumentResponse(self, std, test_path):
        os.makedirs(test_path, exist_ok=True)
        res = ''
        filename = os.path.join(test_path, std.name + '.task2')
        for entity in std.entities:
            if entity.tag != 'unknown':
                res += entity.toTestString() + '\n\n'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(res.strip('\n'))

#########################################################################################
# Misc.

def loadAllStandard(path):
    """Load all standard markup files from the provided directory. Returns a list."""

    names = set([x.split('.')[0] for x in os.listdir(path)])
    res = []
    for name in names:
        if re.match('book_[0-9]+', name) == None:
            continue
        res.append(Standard(name, path))
    
    return sorted(res, key=lambda x: int(x.name[5:]))   # book_XXX - sort by number

def loadAllTest(path):
    """Load all test markup files from the provided directory. Returns a list"""
    names = set(x.split('.')[0] for x in os.listdir(path) if '.task2' in x)
    res = [Test(name, path) for name in names]
    
    return sorted(res, key=lambda x: int(x.name[5:]))   # book_XXX - sort by number

def validateStandard(path):
    """Validate standard markup files and print various stats on .coref layer"""

    std = loadAllStandard(path)

    n_no_coref = 0
    n_no_mention = 0
    n_problematic = 0

    problematic_docs = set()

    n_by_tags = {}
    n_by_attrs = {}

    for s in std:
        has_problematic = False

        if len(s.entities) == 0:
            n_no_coref += 1

        for e in s.entities:
            tag_set = set()
            
            if e.is_problematic:
                n_problematic += 1
                has_problematic = True

            if len(e.mentions) == 0:
                n_no_mention += 1

            # find all mention tags
            for m in e.mentions:
                tag_set.add(m.tag)

            for attr in e.attributes:
                if attr.name in n_by_attrs:
                    n_by_attrs[attr.name] += 1
                else:
                    n_by_attrs[attr.name] = 1
            
            tags = ' '.join(sorted(tag_set, key=lambda x: x))

            if tags in n_by_tags:
                n_by_tags[tags] += 1
            else:
                n_by_tags[tags] = 1

        if has_problematic:
            problematic_docs.add(s.name)

    print('STATISTICS:')
    print('  Loaded {} standard documents'.format(len(std)))
    print('  Found {} documents without .coref layer'.format(n_no_coref))
    print('  Found {} documents with {} entities that have broken links:'.
          format(len(problematic_docs), n_problematic))
    print('    ' + '\n    '.join(problematic_docs))
    print('Object counts by type:')
    for key in n_by_tags.keys():
        print('{} - {}'.format(key, n_by_tags[key]))
    print('Attribute counts by type:')
    for key in n_by_attrs.keys():
        print('{} - {}'.format(key, n_by_attrs[key]))

