

#########################################################################################

class Metrics:
    """Commonly used evaluation metrics"""
    
    header_template = '{:8} {:8} {:8} {:8} {:8} {:8} {:8}'
    line_template = '{:8.4f} {:8.4f} {:8.4f} {:8.2f} {:8.2f} {:8.0f} {:8.0f}'

    def __init__(self):
        """Initialize the empty metrics object"""
        # True positive used in recall calculation
        self.tp_std = 0.0
        # True positive used in precision calculation
        self.tp_test = 0.0
        # Number of standard objects
        self.n_std = 0
        # Number of test objects
        self.n_test = 0
        # Precision
        self.precision = 1.0
        # Recall
        self.recall = 1.0
        # F1
        self.f1 = 1.0

    def recalculate(self):
        self.precision = self.tp_test / self.n_test if self.n_test > 0 else 1.0
        self.recall = self.tp_std / self.n_std if self.n_std > 0 else 1.0

        if self.n_std + self.n_test == 0:
            self.f1 = 1.0
        else:
            denominator = self.precision + self.recall
            self.f1  = (
                (2 * self.precision * self.recall / denominator)
                    if denominator > 0 else 0.0
            )

        isValid = lambda x: x >= 0 and x <= 1
        assert(isValid(self.precision))
        assert(isValid(self.recall))
        assert(isValid(self.f1))

    def add(self, other):
        self.tp_std += other.tp_std
        self.tp_test += other.tp_test
        self.n_std += other.n_std
        self.n_test += other.n_test
        self.recalculate()

    def toLine(self):
        """Returns a line for the stats table"""
        return Metrics.line_template.format(
            self.precision, self.recall, self.f1,
            self.tp_std, self.tp_test, self.n_std, self.n_test)

    @classmethod
    def header(cls):
        """Returns a header for the stats table"""
        return Metrics.header_template.format(
            'P', 'R', 'F1', 'TP1', 'TP2', 'In Std.', 'In Test.')

    @classmethod
    def createSimple(cls, tp, n_std, n_test):
        """Calculate metrics with single TruePositive value"""
        m = cls()

        m.tp_std = tp
        m.tp_test = tp
        m.n_std = n_std
        m.n_test = n_test

        m.recalculate()

        return m
    
    @classmethod
    def create(cls, tp_std, tp_test, n_std, n_test):
        """Calculate metrics with separate TruePositive values"""
        m = cls()

        m.tp_std = tp_std
        m.tp_test = tp_test
        m.n_std = n_std
        m.n_test = n_test

        m.recalculate()

        return m