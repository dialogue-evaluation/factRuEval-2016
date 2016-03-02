# Argument of a fact from the .facts layer of the standard markup
# This module also includes 3 implementations of argument values
# and an argument builder for the standard markup

import os

from dialent.common.util import compareStrings

#########################################################################################

jobs_file_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    '../jobs_processed.txt'
    )

class Argument:
    """Fact argument"""

    # names of the special cyrillic attributes
    special_names = ['сложность', 'модальность', 'фаза']

    # normalized 'occupation:position' values dictionary
    # loaded from a specific file
    position_dict = None

    def __init__(self, name):
        """Initialize"""
        if Argument.position_dict == None:
            Argument.loadPositionDict()

        self.name = name.strip(' \n\r\t').lower()
        if self.name == 'job':
            self.name = 'position'
        self.is_special = self.name in Argument.special_names
        self.values = []
        self.fact = None

    def toTest(self):
        if(len(self.values) == 0):
            print(self.fact)
        return self.name + ' : ' + str(self.values[0])

    def toInlineString(self):
        return str(self.values[0])

    def canMatch(self, other):
        """Check if the value of other is compatable with the arguments own values"""
        assert(len(other.values) == 1) # other should be a test argument with only 1 value
        if self.name != other.name:
            return False

        for x in self.values:
            for y in other.values:
                if x.equals(y):
                    return True

        return False

    def finalize(self):
        """Finalize the argument for evaluation"""
        for v in self.values:
            v.finalize()

    def __repr__(self):
        return self.name + ' : ' + ' | '.join([str(x) for x in self.values])

    def __str__(self):
        return self.__repr__()

    # classmethods

    @classmethod
    def loadPositionDict(cls):
        """Load the normalized 'occupation:position' values dictionary from the
        associated file. This method should only be called once"""
        cls.position_dict = {}
        with open(jobs_file_path, encoding='utf-8') as f:
            for line in f:
                parts = [x.strip(' \n\r\t') for x in line.split('|')]
                assert(len(parts) == 2)
                cls.position_dict[parts[0]] = parts[1]


    @classmethod
    def fromTest(cls, line):
        parts = line.split(':')
        assert(len(parts) == 2)
        arg = cls(parts[0])
        arg.values.append(StringValue(parts[1]))

        return arg


#########################################################################################

class EntityValue:
    """Fact argument that is an entity"""

    def __init__(self, full_id, descr, entity_dict):
        """Initialize the object"""
        assert(full_id.startswith('obj'))
        self.entity = entity_dict[full_id[3:]]
        self.descr = descr.strip(' \n\r\t').lower()
        self.values = set([self.descr])

        # special logic for different types of entities
        assert( self.entity.tag != 'locorg' )
        self.values = self.values.union(self._expandFromText())

        if self.entity.tag == 'per':
            self.values = self.values.union(self._expandPerson(self.entity))

        if self.entity.tag in ['org', 'loc']:
            self.values = self.values.union(self._expandWithDescr(self.entity))

    def equals(self, other):
        assert(isinstance(other, StringValue))
        for val in self.values:
            if compareStrings(val, other.value):
                return True
        return False

    def finalize(self):
        """Finalize the value"""
        self.values = [x.lower().strip(' \n\r\t').replace('ё', 'е') for x in self.values]

    def _expandFromText(self):
        """Returns a set of non-normalized values corresponding to each mention of the
        entity"""
        additional_values = []
        for mention in self.entity.mentions:
            additional_values.append(mention.text)
            additional_values.append(mention.interval_text)
        return set(additional_values)

    def _expandPerson(self, per):
        """Create all possible values for a person"""
        assert(per.tag == 'per')

        firstnames = per.getAttr('firstname')
        lastnames = per.getAttr('lastname')
        patronymics = per.getAttr('patronymic')
        nicknames = per.getAttr('nickname')

        lists = [firstnames, lastnames, patronymics, nicknames]
        combinations = ['lfp', 'fpl', 'fp', 'fl', 'lf', 'n', 'f', 'p', 'l', 'fn']
            
        values = []
        for c in combinations:
            values += self._buildPerValues(lists, c)
        values.append(self.descr)
        return set(values)

    def _buildPerValues(self, lists, combination):
        value_lists = []
        for symbol in combination:
            if symbol == 'f':
                value_lists.append(lists[0])
            elif symbol == 'l':
                value_lists.append(lists[1])
            elif symbol == 'p':
                value_lists.append(lists[2])
            elif symbol == 'n':
                value_lists.append(lists[3])
        return self._combine(value_lists)
        
    def _combine(self, value_lists):
        options = ['']
        new_options = []
        for lst in value_lists:
            for val in lst:
                if val == '':
                    continue
                for opt in options:
                    new_options.append(opt + ' ' + val if opt != '' else val)
            options = new_options
            new_options = []
        return options

    def _expandWithDescr(self, org):
        """Replace the value list with all possible organization/location names"""
        assert(org.tag in ['org', 'loc'])
        return set(org.getAttr('name'))
        
    def expandWithIsPartOf(self, ent_dict):
        if not (self.entity in ent_dict):
            return

        for ent in ent_dict[self.entity]:
            self.values = self.values.union(self._expandWithDescr(ent))

    def __repr__(self):
        return self.descr

    def __str__(self):
        return self.__repr__()

#########################################################################################

class SpanValue:
    """Fact argument that is a span"""

    def __init__(self, owner, full_id, descr, span_dict):
        """Initialize the object"""
        assert(full_id.startswith('span'))
        self.owner = owner
        self.span = span_dict[full_id[4:]]
        self.values = [self.span.text]
        self.descr = self.span.text

    def equals(self, other):
        for val in self.values:
            if compareStrings(val, other.value):
                return True
        return False

    def finalize(self):
        """Finalize the value"""
        if self.owner.name == 'position':
            if(self.values[0] in Argument.position_dict):
                self.values.append(Argument.position_dict[self.values[0]])
        self.values = [x.lower().strip(' \n\r\t').replace('ё', 'е') for x in self.values]

    def __repr__(self):
        return self.descr

    def __str__(self):
        return self.__repr__()

#########################################################################################

class StringValue:
    """String value for special cases"""

    def __init__(self, value):
        """Initialie the object"""
        self.value = value.strip(' \n\r\t').lower()
        self.descr = self.value

    def equals(self, other):
        # STUB
        return compareStrings(self.value, other.value)

    def finalize(self):
        """Finalize the value"""
        self.value = self.value.lower().strip(' \n\r\t').replace('ё', 'е')
        # does nothing for now

    def __repr__(self):
        return self.descr

    def __str__(self):
        return self.descr

#########################################################################################

class ArgumentBuilder:
    """Creates an argument of a proper type from string"""

    def __init__(self, entity_dict, span_dict):
        self.entity_dict = entity_dict
        self.span_dict = span_dict

    def build(self, line):
        parts = line.split(' ')
        name = parts[0].lower()
        alternatives = ' '.join(parts[1:]).split('|')
        argument = Argument(name)

        assert(len(alternatives)>0)

        if parts[1].startswith('span'):
            # spans have the following syntax:
            # position spanXXXX somevalue | spanYYYY someothervalue
            for alternative in alternatives:
                parts = [x for x in alternative.split(' ') if x != '']
                argument.values.append(
                    SpanValue(argument, parts[0], ' '.join(parts[1:]), self.span_dict))
        elif parts[1].startswith('obj'):
            # objects have different syntax:
            # who objXXX name1 | name2 | name3
            # (all names refer to the same object)
            argument.values.append(
                EntityValue(parts[1], ' '.join(parts[2:]), self.entity_dict))
        else:
            # just a string value
            for alternative in alternatives:
                argument.values.append(StringValue(alternative))

        return argument

