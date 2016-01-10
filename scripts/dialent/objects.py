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
    

#########################################################################################

class Entity:
    """Entity consisting of spans"""
    
    def __init__(self, id, tag, span_ids, span_dict):
        """Create a new entity of a given type with the provided spans"""
        self.id = int(id)
        
        if not tag in Config.STANDARD_TYPES:
            raise Exception('Unknown entity tag: {}'.format(tag))
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


#########################################################################################

class Interval:
    """Text interval"""
    
    def __init__(self, start, length):
        self.start = int(start)
        self.length = int(length)
        self.end = self.start + self.length - 1
        
    def __repr__(self):
        return '<{}; {}>'.format(self.start, self.end)
    
#########################################################################################

class TokenSet:
    """A set of tokens corresponding to an object"""
    
    def __init__(self, token_list, tag):
        self.tokens = set(token_list)
        self.tag = tag
        self.is_embedded = False
        self._span_marks = {}
        
    def __repr__(self):
        return '<' + ' '.join([repr(x) for x in self.sortedTokens()]) + '>'
    
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
        """Creates an interval for the response generator"""
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
        """Returns the span mark for this token"""
        if token not in self._span_marks:
            return 'none'
        else:
            return self._span_marks[token]
        
    def setMark(self, token, mark):
        """Sets the span mark for the given token"""
        self._span_marks[token] = mark
