# Various auxilliary data objects used in dialent

########################################################################################

from dialent.config import Config

#########################################################################################

class Token:
    """Raw token"""
    
    def __init__(self, id, start, length, text):
        """Create a new token with the given parameters"""
        self.id = int(id)
        self.start = int(start)
        self.length = int(length)
        self.end = self.start + self.length - 1
        self.text = text
        self.next = None
        self.prev = None        
        
    def __repr__(self):
        return '{}[{}-{}, #{}]'.format(
            self.text, self.start, self.end, self.id)

    def __str__(self):
        return repr(self)
    
    def isIgnored(self):
        """Check if this token should be ignored during the comparison.
        The comparison is supposed to ignore the punctuation tokens that are(presumably)
        located directly next to their neighboors"""
        
        return self.length == 1 and (self.prev != None and self.start - self.prev.end == 1
                or self.next != None and self.next.start - self.end == 1)


#########################################################################################

class Span:
    """Raw span"""
    
    def __init__(self, id, tag, start, nchars, token_start, ntokens):
        """Create a new span with the given parameters"""
        self.id = int(id)
        self.tag = tag
        
        self.start = int(start)
        self.end = int(start) + int(nchars)
        
        self.token_start = int(token_start)
        self.ntokens = int(ntokens)
        
        self.tokens = []
        self.text = ''
        
    def __repr__(self):
        return '{}[{} #{}],  ntokens={}'.format(
            self.text, self.tag, self.id, self.ntokens)

    def __str__(self):
        return repr(self)

    

#########################################################################################

class Mention:
    """Mention consisting of spans"""
    
    def __init__(self, id, tag, span_ids, span_dict):
        """Create a new mention of a given type with the provided spans"""
        self.id = int(id)
        
        if not tag in Config.STANDARD_TYPES:
            raise Exception('Unknown mention tag: {}'.format(tag))
        self.tag = Config.STANDARD_TYPES[tag]
        
        self.spans = []
        for id in span_ids:
            self.spans.append(span_dict[id])
        
    def __repr__(self):
        res = '{} #{}:\n'.format(self.tag, self.id)
        for span in self.spans:
            res += '\t{} : {}\n'.format(span.tag, span.text)
        res += '\n'
        return res

    def __str__(self):
        return repr(self)



#########################################################################################

class Interval:
    """Text interval"""
    
    def __init__(self, start, length):
        self.start = int(start)
        self.length = int(length)
        self.end = self.start + self.length - 1
        
    def __repr__(self):
        return '<{}; {}>'.format(self.start, self.end)

    def __str__(self):
        return repr(self)

    
#########################################################################################

class TokenSet:
    """A set of tokens corresponding to an object"""
    
    def __init__(self, token_list, tag):
        self.tokens = set(token_list)
        self.tag = tag
        self.parents = []
        self._span_marks = dict([(x, 0) for x in self.tokens])
        
    def __repr__(self):
        return '<' + ' '.join([repr(x) for x in self.sortedTokens()]) + '>'

    def __str__(self):
        return repr(self)

    def sortedTokens(self):
        """Make a list of tokens sorted by their starting position"""
        return sorted(self.tokens, key=lambda x: x.start)
    
    def getHoles(self):
        """Return tokens not present in the set but located between
        the included tokens in the text"""
        
        res = []
        for i, token in enumerate(self.sortedTokens()):
            if i != len(self.tokens) - 1:
                t = token.next
                hole = []
                while not t in self.tokens:
                    hole.append(t)
                    t = t.next
                if len(hole) > 0:
                    res.append(hole)
        return res
    
    def intersects(self, other):
        """Check for an intersection with the other TokenSet"""
        return len(self.tokens.intersection(other.tokens)) > 0
    
    def toInterval(self):
        """Create an interval for the response generator"""
        t = self.sortedTokens()
        
        # try to include quotes on the left and any punctuation on the right
        start_token = t[0]
        end_token = t[len(t)-1]
        while start_token.prev != None and start_token.prev.isIgnored():
            start_token = start_token.prev
        while end_token.next != None and end_token.next.isIgnored():
            end_token = end_token.next
        
        start = start_token.start
        end = end_token.end
        length = end - start + 1
        return Interval(start, length)
        
    def mark(self, token):
        """Return the span mark for this token"""
        if token not in self._span_marks:
            return 'none'
        else:
            return self._span_marks[token]
        
    def setMark(self, token, mark):
        """Try to increase the mark of the given token"""
        if(self._span_marks[token] < mark):
            self._span_marks[token] = mark

    def isEmbedded(self):
        """Only true if this object is embedded into another object"""
        return len(self.parents)>0

    def findParents(self, all_token_sets):
        """Fill the parent list of the current token set"""
        self.parents = []
        for other in all_token_sets:
            if other is self:
                # all_token_sets can include this set as well
                continue

            if self.tokens.issubset(other.tokens):
                self.parents.append(other)

#########################################################################################

class Attribute:
    """Entity attribute with one or several synonimous values"""

    def __init__(self):
        self.name = ''
        self.value = ''

    # static build methods:
    @classmethod
    def fromStandard(cls, lines):
        """Load an attribute from the set of lines representing it.
        This method corresponds to the standard format of representation
        
        Returns a new Attribute instance"""

        assert(len(lines) == 1)

        line = lines[0]
        parts = line.split(' ')

        instance = cls()
        instance.name = parts[0].strip().lower()
        instance.value = ' '.join(parts[1:]).lower()
        instance.value.replace('\u0401', '\u0435') # make all 'e'-s uniform

        return instance

    @classmethod
    def fromTest(cls, line):
        """Load an attribute from the set of lines representing it.
        This method corresponds to the test format of representation.
        
        Returns a new Attribute instance"""

        parts = line.split(':')
        assert(len(parts) == 2)

        instance = cls()
        instance.name = parts[0].strip().lower()
        instance.value = parts[1].strip().lower()
        instance.value.replace('\u0401', '\u0435') # make all 'e'-s uniform

        return instance
        
    def matches(self, other):
        """Returns true if a set of value of other corresponds to a set of values of this"""
        # TODO this is a stub to be reworked after the export format is finalized
        return self.name == other.name and self.value == other.value

    def toTestString(self):
        """Creates a test representation of this attribute"""

        return '{} : {}'.format(self.name, self.value)

    def __repr__(self):
        return '{} : {}'.format(self.name, self.value)

    def __str__(self):
        return self.__repr__()

class Entity:
    """Entity with a set of attributes, assembled from several mentions throughout the
    document"""

    def __init__(self):
        
        self.attributes = []
        self.id = -1
        self.tag = 'unknown'
        self.spans = []
        self.mentions = []
        self.is_problematic = False

    # static build methods
    @classmethod
    def fromStandard(cls, text, mention_dict, span_dict):
        """Load the entity from a block of text of the following format
        
        [entity_id][ (span_id|mention_id)]+
        [attr_name] [attr_value]
        ...
        [attr_name] [attr_value]

        mention_dict - mention_id -> mention
        span_dict - span_id -> span
        """

        assert(len(text.strip('\r\n\t ')) > 0)
        lines = text.split('\n')

        instance = cls()
        for line in lines[1:]:
            if len(line) == 0:
                continue
            instance.attributes.append(Attribute.fromStandard([line]))
        instance._load_id_line(lines[0], mention_dict, span_dict)

        return instance

    @classmethod
    def fromTest(cls, text):
        """Load the entity from a test file using a different format:
        
        [entity_type]
        [attr_name]:[attr_value]
        ...
        [attr_name]:[attr_value]
        """

        assert(len(text.strip('\r\n\t ')) > 0)

        instance = cls()

        lines = text.split('\n')
        for line in lines[1:]:
            if len(line) == 0:
                continue
            instance.attributes.append(Attribute.fromTest(line))
        instance.tag = lines[0].lower()

        return instance

    def toTestString(self):
        """Creates a test representation of this entity"""
        res = self.tag
        for attr in self.attributes:
            res += '\n' + attr.toTestString()

        return res

    def _load_id_line(self, line, mention_dict, span_dict):
        """Load ids from the first line of the standard representation"""
        str_ids = line.strip(' \n\r\t').split(' ')
        self.id = int(str_ids[0])

        self.is_problematic = False
        
        for _some_id in str_ids[1:]:
            some_id = int(_some_id)
            if some_id in mention_dict:
                assert(not some_id in span_dict)
                mention = mention_dict[some_id]
                if not mention in self.mentions:
                    self.mentions.append(mention)
            elif some_id in span_dict:
                assert(not some_id in mention_dict)
                span = span_dict[some_id]
                if not span in self.spans:
                    self.spans.append(span)
            else:
                self.is_problematic = True
                print('FOUND PROBLEMATIC ENTITY: {} has no {}'.format(self, some_id))

        # it is not actually the case, at least for now
        # but arguably it should be
        # assert(len(self.mentions) > 0)
        
        if len(self.mentions) > 0:
            self.tag = self.mentions[0].tag

    def __repr__(self):
        res = ''
        res += '{} #{}'.format(self.tag, self.id)
        for attribute in self.attributes:
            res += '\n  {}'.format(attribute)
        return res

    def __str__(self):
        return self.__repr__()
