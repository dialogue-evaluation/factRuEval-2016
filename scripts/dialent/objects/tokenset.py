# Tokenset is a set of tokens corresponding to an object used in task 1 evaluation

from dialent.config import Tables

from dialent.objects.token import Token
from dialent.objects.interval import Interval

#########################################################################################

class TokenSet:
    """A set of tokens corresponding to an object"""
    
    def __init__(self, token_list, tag, text):
        self.id = -1
        self.tokens = set(token_list)
        self.tag = tag
        self.parents = []
        self.interval = None
        self._span_marks = dict([(x, 0) for x in self.tokens])
        self.text = text
        self.is_ignored_sibling = False
        
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
        if self.interval != None:
            return self.interval

        t = self.sortedTokens()
        
        # try to include quotes on the left and any punctuation on the right
        if len(t) == 0:
            print(self)
        start_token = t[0]
        end_token = t[len(t)-1]
        
        while start_token.prev != None and start_token.prev.text == '"':
                start_token = start_token.prev
        while end_token.next != None and end_token.next.text == '"':
                end_token = end_token.next
        
        start = start_token.start
        end = end_token.end
        length = end - start + 1
        return Interval(start, length)

    def isUnnamed(self):
        """Returns True if the object is unnamed and must be ignored.
        In practice it means that no token of the set is marked with a span of value>0"""
        for key in self._span_marks:
            if self._span_marks[key] > 0:
                return False
        return True
        
    def mark(self, token):
        """Return the span mark for this token"""
        if token not in self._span_marks:
            return 0
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
        """Fill the parent and sibling lists of the current token set"""
        self.parents = []
        self.siblings = []
        for other in [x for x in all_token_sets
                        if x.tag in Tables.PARENT_TAGS[self.tag]]:
            if other is self:
                # all_token_sets can include this set as well
                continue

            if self.tokens < other.tokens:
                self.parents.append(other)
            elif self.tokens == other.tokens:
                self.siblings.append(other)

    def toInlineString(self):
        """Make an inline representation using the tokensets interval"""
        i = self.toInterval()
        return (self.tag.upper()
                + (' {}'.format(self.id) if self.id != -1 else '')
                + ' {} "{}"'.format(i, self.text[i.start:i.end+1]))
