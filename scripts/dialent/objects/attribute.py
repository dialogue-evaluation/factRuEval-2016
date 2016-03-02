# Attribute of an entity from the .coref layer of the standard markup

from dialent.common.util import compareStrings
from dialent.common.util import normalize

#########################################################################################

class Attribute:
    """Entity attribute with one or several synonimous values"""

    def __init__(self):
        """Create a new object. Do not call this directly, use classmethods instead."""
        self.name = ''
        self.values = set()

    def buildAlternatives(self, descr):
        """Build full alternative list from current values and descriptors."""
        raw_values = self.values
        self.values = set()
        for x in raw_values:
            for y in descr.values:
                self.values.add(x)
                if (' ' + y + ' ') in (' ' + x + ' '):
                    # for those descriptors already included in a name
                    # added spaces to do a full-word search
                    continue

                self.values.add(x + ' ' + y)
                self.values.add(y + ' ' + x)

    def tryPutInQoutes(self, entity):
        """Try to return a copy of this attribute surrounded with quotes.
        This must only yield meaningful result if the entity this attribute belongs to
        has a span marked as '**_name' surrounded by qoutes"""

        # method must only be called before all other processing
        assert(len(self.values) == 1)

        if entity.tag == 'per':
            return

        val = list(self.values)[0]
        all_spans = []
        all_spans.extend(entity.spans)
        for mention in entity.mentions:
            all_spans.extend(mention.spans)
        name_spans = [x for x in all_spans
                      if x.text.lower().replace('ё', 'е') == val and 'name' in x.tag]

        for span in name_spans:
            if span.isInQuotes():
                attr = Attribute()
                attr.name = self.name
                attr.values.add(span.getLeftQuote() + val + span.getRightQuote())
                return attr

        return

    def trimName(self):
        """Removes any digits following the attribute name"""
        self.name = self.name.strip('1234567890')
        
    def matches(self, other):
        """Returns true if a set of value of other corresponds to a set of values of this"""
        if self.name != other.name:
           return False
      
        for v1 in self.values:
            for v2 in other.values:
                if compareStrings(v1, v2):
                    return True

        return False

    def isValid(self):
        """Checks if the attribute is valid (has non-empty values)"""
        for value in self.values:
            if len(value) > 0:
                return True

        return False

    def toTestString(self):
        """Creates a test representation of this attribute"""
        return '\n'.join(['{} : {}'.format(self.name, x) for x in self.values])

    def __repr__(self):
        return '{} : {}'.format(self.name, ' | '.join( self.values ))

    def __str__(self):
        return self.__repr__()


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
        value = normalize(' '.join(parts[1:]))
        instance.values.add(value)

        return instance

    @classmethod
    def fromTest(cls, line):
        """Load an attribute from the set of lines representing it.
        This method corresponds to the test format of representation.
        
        Returns a new Attribute instance"""

        parts = line.split(':')
        assert(len(parts) >= 2)

        instance = cls()
        instance.name = parts[0].strip().lower()
        value = normalize(':'.join(parts[1:]))
        instance.values.add(value)

        return instance

    @classmethod
    def merge(cls, attr_list, new_name):
        """Merge values from the list of attributes, and assign a new name. Returns a new
        instance"""

        instance = cls()
        instance.name = new_name
        for attr in attr_list:
            instance.values.update(attr.values)

        return instance
