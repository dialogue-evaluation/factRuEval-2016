# Representation of a token from the standard markup .tokens layer

from dialent.common.util import normalize

#########################################################################################

class Token:
    """Raw token"""
    
    def __init__(self, id, start, length, text):
        """Create a new token with the given parameters"""
        self.id = id
        self.start = int(start)
        self.length = int(length)
        self.end = self.start + self.length - 1
        self.text = normalize(text)
        self.next = None
        self.prev = None        
        
    def __repr__(self):
        return '{}[{}-{}, #{}]'.format(
            self.text, self.start, self.end, self.id)

    def __str__(self):
        return repr(self)
    
    def isLetter(self):
        """Check if this token is a single letter"""
        if len(self.text) > 1:
            return False
        return self.text.upper() != self.text or self.text.lower() != self.text

    def isPunctuation(self):
        """Check if this token is punctuation. Only checks for a limited amount of
        symbols because this method is only called to detect a small amount of special
        occasions in standard markup"""
        return len(self.text) == 1 and not self.isLetter()

    def isIgnored(self):
        """Check if this token should be ignored during the comparison.
        The comparison is supposed to ignore the punctuation tokens that are(presumably)
        located directly next to their neighboors"""
        
        return self.length == 1 and not self.isLetter() and (
            self.prev != None and self.start - self.prev.end == 1
                or self.next != None and self.next.start - self.end == 1)

    def isIgnoredFromLeft(self):
        """Check if this token should be ignored during the comparison. In this case the
        token must be directly next to its prev. neighbour"""
        return self.length == 1 and not self.isLetter() and (
            self.prev != None and self.start - self.prev.end == 1)

    def isIgnoredFromRight(self):
        """Check if this token should be ignored during the comparison. In this case the
        token must be directly next to its next. neighbour"""
        return self.length == 1 and not self.isLetter() and (
            self.next != None and self.next.start - self.end == 1)
