# Representation of a span from the standard markup .spans layer

#########################################################################################

class Span:
    """Raw span"""
    
    def __init__(self, id, tag, start, nchars, token_start, ntokens):
        """Create a new span with the given parameters"""
        self.id = id
        self.tag = tag
        
        self.start = int(start)
        self.end = int(start) + int(nchars)
        
        self.token_start = int(token_start)
        self.ntokens = int(ntokens)
        
        self.tokens = []
        self.text = ''

    def isInQuotes(self):
        """Check if the span is preceded by an opening quote and succeeded by a closing
        one"""

        lq = self.getLeftQuote()
        rq = self.getRightQuote()

        return (lq + rq) in ['""', "''", '«»']

        return self.getLeftQuote() != '' and self.getLeftQuote() == self.getRightQuote()

    def getLeftQuote(self):
        """Find and return quote preceding the span. If there is no quote, returns ''"""
        # tokens are always sorted
        assert(len(self.tokens) > 0)
        prev = self.tokens[0].prev
        if prev != None and prev.text in ['"', "'", "«"]:
            return prev.text
        else:
            return ''

    def getRightQuote(self):
        """Find and return quote succeeding the span. If there is no quote, returns ''"""
        # tokens are always sorted
        assert(len(self.tokens) > 0)
        next = self.tokens[-1].next
        if next != None and next.text in ['"', "'", "»"]:
            return next.text
        else:
            return ''

        
    def __repr__(self):
        return '{}[{} #{}],  ntokens={}'.format(
            self.text, self.tag, self.id, self.ntokens)

    def __str__(self):
        return repr(self)
