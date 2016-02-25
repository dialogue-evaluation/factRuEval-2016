# Text interval for track 1 test files and reports

#########################################################################################

class Interval:
    """Text interval"""
    
    def __init__(self, start, length):
        """Create an interval with the given starting position and length."""
        self.start = int(start)
        self.length = int(length)
        self.end = self.start + self.length - 1
        
    def __repr__(self):
        return '<{}; {}>'.format(self.start, self.end)

    def __str__(self):
        return repr(self)
