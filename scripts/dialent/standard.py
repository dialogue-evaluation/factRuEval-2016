# This module deals primarily with the standard markup representation

import os
import csv

from dialent.config import Config, Tables

from dialent.objects.token import Token
from dialent.objects.span import Span
from dialent.objects.mention import Mention
from dialent.objects.entity import Entity
from dialent.objects.fact import Fact
from dialent.objects.interval import Interval
from dialent.objects.tokenset import TokenSet

from dialent.common.util import normalize
from dialent.common.util import safeNormalize

#########################################################################################

class Standard:
    """Standard document data loaded from a set of export files.
    
    The set currently includes:
     - 'NAME.txt'
     - 'NAME.tokens'
     - 'NAME.spans'
     - 'NAME.objects'
     - 'NAME.coref'
     - 'NAME.facts'
     """
    
    def __init__(self, name, path='.'):
        self.name = name
        try:
            self.has_coref = True
            self.has_facts = True
            full_name = os.path.join(path, name)
            self.loadText(full_name + '.txt')
            self.loadTokens(full_name + '.tokens')
            self.loadSpans(full_name + '.spans')
            self.loadMentions(full_name + '.objects')
            self.loadCoreference(full_name + '.coref')
            self.loadFacts(full_name + '.facts')
        except Exception as e:
            print('Failed to load the standard of {}:'.format(name))
            print(e)
            # reset the document so it has no impact on the comparison
            self.mentions = []
            self.entities = []
            self.facts = []
    
    def loadTokens(self, filename):
        """Load the data from a file with the provided name
        
        Raw token data should be loaded from one of the system export '.tokens' file"""
        self.tokens = []
        
        with open(filename, 'r', encoding='utf-8') as f:
            rdr = csv.reader(f, delimiter=Config.DEFAULT_DELIMITER, quotechar=Config.QUOTECHAR)
            
            for index, line in enumerate(rdr):
                if len(line) == 0:
                    # skip the empty lines
                    continue
                
                if len(line) != Config.TOKEN_LINE_LENGTH:
                    # bad non-empty line
                    raise Exception(
                        'Wrong length in line {} of file {}'.format(
                            index, filename))
                
                self.tokens.append(
                    Token(*line) )

        # fill the token dictionary
        self._token_dict = dict([(x.id, x) for x in self.tokens])
        
        # set neighboor links in tokens
        self.tokens = sorted(self.tokens, key=lambda x: x.start)
        for i, token in enumerate(self.tokens):
            if i != 0:
                token.prev = self.tokens[i-1]
            if i != len(self.tokens)-1:
                token.next = self.tokens[i+1]

                
    def loadSpans(self, filename):
        """Load the data from a file with the provided name
        
        Raw span data should be loaded from one of the system export '.spans' file
        
        Expected format:
        line = <left> SPAN_FILE_SEPARATOR <right>
        left = <span_id> <tag_name> <start_pos> <nchars> <start_token> <ntokens>
        right ::= [ <token>]+ [ <token_text>]+     // <ntokens> of each
            """
        self.spans = []
        
        with open(filename, 'r', encoding='utf-8') as f:
            for index, line in enumerate(f):
                if len(line) == 0:
                    # skip the empty lines
                    continue
                
                parts = line.split(Config.SPAN_FILE_SEPARATOR)
                if len(parts) != 2:
                    # bad non-empty line
                    raise Exception(
                        'Expected symbol "{}" missing in line {} of file {}'.format(
                            Config.SPAN_FILE_SEPARATOR, index, filename))
                    
                left = parts[0]
                right = parts[1]
                
                filtered_left = [i
                     for i in left.split(Config.DEFAULT_DELIMITER)
                         if len(i) > 0]
                
                if len(filtered_left) < 6:
                    raise Exception(
                        'Missing left parts in line {} of file {}'.format(
                            index, filename))
                    
                new_span = Span(*filtered_left)
                
                filtered_right = [i
                      for i in right.split(Config.DEFAULT_DELIMITER)
                            if len(i) > 0]
                if len(filtered_right) != 2*new_span.ntokens:
                    raise Exception(
                        'Missing right parts in line {} of file {}'.format(
                            index, filename))
                
                
                token_ids = [x.strip() for x in filtered_right[:new_span.ntokens]]
                new_span.tokens = sorted([self._token_dict[x] for x in token_ids],
                                         key=lambda x: x.start)
                new_span.text = normalize(' '.join(filtered_right[new_span.ntokens:]))
                new_span.text = new_span.text.replace('\n', '')
                
                self.spans.append(new_span)
                
        # fill the span dictionary
        self._span_dict = dict([(x.id, x) for x in self.spans])

    def loadMentions(self, filename):
        """Load the data from a given 'objects' file. Expected format:
        
        line = <object_id> <type> <span_id> # <comment>
        """
        
        self.mentions = []
        with open(filename, 'r', encoding='utf-8') as f:
            r = csv.reader(f, delimiter=' ', quotechar=Config.QUOTECHAR)
            for index, line in enumerate(r):
                if Config.COMMENT_SEPARATOR in line:
                    comment_index = line.index(Config.COMMENT_SEPARATOR)
                    line = line[:comment_index]

                if len(line) == 0:
                    continue
                
                if len(line) <= 2:
                    raise Exception(
                        'Missing spans in object description: line {} of file {}'.format(
                            index, filename))
                
                try:
                    mention_id = line[0].strip()
                    span_indices = [descr.strip() for descr in line[2:]]
                except Exception as e:
                    raise Exception('Invalid mention or span id: line {} of file {}:\n{}'.format(
                        index, filename, e))

                self.mentions.append(
                    Mention(mention_id, line[1], span_indices, self._span_dict))
                
        # fill the mention dictionary
        self._mention_dict = dict([(x.id, x) for x in self.mentions])
        for m in self.mentions:
            m.findParents(self.mentions)
            m.setText(self.text)

    def loadCoreference(self, filename):
        """Load coreference data from the associated file"""
        self.entities = []

        try:
            open(filename, 'r', encoding='utf-8')
        except:
            # there are currently some documents with no .coref layer. This is temporary
            self.has_coref = False
            return
        
        with open(filename, 'r', encoding='utf-8') as f:
            buffer = ''
            for raw_line in f:
                line = raw_line.strip(' \t\n\r')
                if len(line) == 0:
                    if len(buffer) > 0:
                        e = Entity.fromStandard(buffer, self._mention_dict, self._span_dict)
                        self.entities.append(e)
                        buffer = ''
                else:
                    buffer += line + '\n'
                
            if len(buffer) > 0:
                self.entities.append(Entity.fromStandard(buffer, self._mention_dict, self._span_dict))

        self._entity_dict = {}
        for ent in self.entities:
            self._entity_dict[ent.id] = ent

    def loadFacts(self, filename):
        """Load facts from the associated file"""
        self.facts = []

        try:
            open(filename, 'r', encoding='utf-8')
        except:
            # there are currently some documents with no .coref layer. This is temporary
            self.has_facts = False
            return
        
        with open(filename, 'r', encoding='utf-8') as f:
            buffer = ''
            for raw_line in f:
                line = raw_line.strip(' \t\n\r')
                if len(line) == 0:
                    if len(buffer) > 0:
                        e = Fact.fromStandard(buffer, self._entity_dict, self._span_dict)
                        self.facts.append(e)
                        buffer = ''
                else:
                    buffer += line + '\n'

            if len(buffer) > 0:
                self.facts.append(Fact.fromStandard(buffer, self._entity_dict, self._span_dict))

        part_of_facts = [f for f in self.facts if f.tag == 'ispartof']
        for fact in self.facts:
            fact.expandWithIsPartOf(part_of_facts)

    def loadText(self, filename):
        """Load text from the associated text file"""
        with open(filename, 'r', encoding='utf-8') as f:
            self.text = safeNormalize(''.join( [line for line in f] ))
            
    def makeTokenSets(self, is_locorg_allowed=True):
        """Create a dictionary of typed TokenSet objects corresponding to the mentions
        
        is_locorg_allowed - enable/disable 'LocOrg' tag"""
        
        # determine what tags are allowed
        allowed_tags = set(['org', 'per', 'loc'])
        if is_locorg_allowed:
            allowed_tags.add('locorg')
            
        res = []
        for mention in self.mentions:
            key = mention.tag
            if key == 'locorg' and not is_locorg_allowed:
                key = 'loc'
            if not (key in allowed_tags):
                continue
            ts = TokenSet(
                    [x for span in mention.spans for x in span.tokens],
                    key, self.text)

            ts.id = mention.id

            for span in mention.spans:
                for token in span.tokens:
                    mark = Tables.getMark(ts.tag, span.tag)
                    ts.setMark(token, mark)
            res.append(ts)

        # find and mark embedded objects
        for obj in res:
            obj.findParents(res)

        return res