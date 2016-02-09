# Various auxilliary data objects used in dialent

########################################################################################

from dialent.config import Config

#########################################################################################

class Token:
    """Raw token"""
    
    def __init__(self, id, start, length, text):
        """Create a new token with the given parameters"""
        self.id = id
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
    
    def isLetter(self):
        if len(self.text) > 1:
            return False
        return self.text.upper() != self.text or self.text.lower() != self.text

    def isPunctuation(self):
        """Check if this token is punctuation. Only checks for a limited amount of
        symbols because this method is only called to detect a small amount of special
        occasions in standard markup"""
        return not self.isLetter()

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
        self.id = id
        
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
    
    def __init__(self, token_list, tag, text):
        self.id = -1
        self.tokens = set(token_list)
        self.tag = tag
        self.parents = []
        self.interval = None
        self._span_marks = dict([(x, 0) for x in self.tokens])
        self.text = text
        
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
        
        while start_token.prev != None and start_token.prev.isIgnoredFromRight():
                start_token = start_token.prev
        while end_token.next != None and end_token.next.isIgnoredFromLeft():
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

    def toInlineString(self):
        """Make an inline representation using the tokensets interval"""
        i = self.toInterval()
        return self.tag.upper() + ' {} "{}"'.format(i, self.text[i.start:i.end+1])

#########################################################################################

class Attribute:
    """Entity attribute with one or several synonimous values"""

    def __init__(self):
        self.name = ''
        self.values = set()

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
        value = ' '.join(parts[1:]).lower()
        value.replace('\u0401', '\u0435') # make all 'e'-s uniform
        instance.values.add(value)

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
        value = parts[1].strip().lower()
        value.replace('\u0401', '\u0435') # make all 'e'-s uniform
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

    def trimName(self):
        """Removes any digits following the attribute name"""
        self.name = self.name.strip('1234567890')
        
    def matches(self, other):
        """Returns true if a set of value of other corresponds to a set of values of this"""
        return self.name == other.name and len(self.values.intersection(other.values)) > 0

    def toTestString(self):
        """Creates a test representation of this attribute"""
        return '\n'.join(['{} : {}'.format(self.name, x) for x in self.values])

    def __repr__(self):
        return '{} : {}'.format(self.name, ' | '.join( self.values ))

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

        instance.processAttributes()
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
        if instance.tag == 'locorg':
            # all locorgs are considered locs for this task
            instance.tag = 'loc'

        return instance

    def processAttributes(self):
        """Merge attributes with similar names, remove suffixes from the names and create
        alternatives"""
        raw_attributes = self.attributes
        self.attributes = []
        names = set([x.name for x in raw_attributes])
        descriptors = []

        # Merge all attributes of the same name into alternatives, except descriptors
        for name in names:
            attr_by_name = [x for x in raw_attributes if x.name == name]
            if name.endswith('descr') or name.endswith('descriptor'):
                descriptors.extend(attr_by_name)
            elif name != 'wikidata':
                # wikidata must be ignored for all the tracks
                self.attributes.append(Attribute.merge(attr_by_name, name))

        # Add descriptors to the list of alternatives
        if len(descriptors) > 0:
            descr = Attribute.merge(descriptors, 'descr')
            for attr in self.attributes:
                attr.buildAlternatives(descr)

        # Trim names ending with digits
        for attr in self.attributes:
            attr.trimName()

    def toInlineString(self):
        """Creates an inline description of this entity"""
        res = self.tag.upper()
        res += ' [' + ', '.join([str(x) for x in self.attributes]) + ']'

        return res

    def toTestString(self):
        """Creates a test representation of this entity"""
        res = self.tag
        for attr in self.attributes:
            res += '\n' + attr.toTestString()

        return res

    def _load_id_line(self, line, mention_dict, span_dict):
        """Load ids from the first line of the standard representation"""
        str_ids = line.strip(' \n\r\t').split(' ')
        self.id = str_ids[0]

        self.is_problematic = False
        
        for _some_id in str_ids[1:]:
            some_id = _some_id
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
        
        tags = set([x.tag for x in self.mentions])
        if len(tags) > 1 and ('locorg' in tags or 'loc' in tags):
            # for this task all locorg objects are condidered loc
            self.tag = 'loc'
        else:
            # there can be no other mutlitype entities
            assert(len(tags)==1)
            self.tag = tags.pop()
            
            if self.tag == 'locorg':
                self.tag = 'loc'

    def __repr__(self):
        res = ''
        res += '{} #{}'.format(self.tag, self.id)
        for attribute in self.attributes:
            res += '\n  {}'.format(attribute)
        return res

    def __str__(self):
        return self.__repr__()

#########################################################################################

class Argument:
    """Fact argument"""

    special_names = ['сложность', 'модальность', 'фаза']

    position_dict = None

    def __init__(self, name):
        """Initialize"""
        if Argument.position_dict == None:
            Argument.loadPositionDict()

        self.name = name.strip(' \n\r\t').lower()
        self.is_special = self.name in Argument.special_names
        self.values = []
        self.fact = None

    def __repr__(self):
        return self.name + ' : ' + ' | '.join([str(x) for x in self.values])

    def __str__(self):
        return self.__repr__()

    @classmethod
    def loadPositionDict(cls):
        cls.position_dict = {}
        with open('dialent/jobs_processed.txt', encoding='utf-8') as f:
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

    def toTest(self):
        if(len(self.values) == 0):
            print(self.fact)
        return self.name + ' : ' + str(self.values[0])

    def toInlineString(self):
        return str(self.values[0])

    def canMatch(self, other):
        """Check if the value of other is compatable with the arguments own values"""
        assert(len(other.values) == 1) # other should be a test argument with only 1 value
        for x in self.values:
            for y in other.values:
                if x.equals(y):
                    return True

        return False

    def finalize(self):
        """Finalize the argument for evaluation"""
        for v in self.values:
            v.finalize()

class EntityValue:
    """Fact argument that is an entity"""

    def __init__(self, full_id, descr, entity_dict):
        """Initialize the object"""
        assert(full_id.startswith('obj'))
        self.entity = entity_dict[full_id[3:]]
        self.descr = descr.strip(' \n\r\t').lower()
        self.values = set([self.descr])

        if self.entity.tag == 'per':
            self._expandPerson()

    def __repr__(self):
        return self.descr

    def __str__(self):
        return self.__repr__()

    def equals(self, other):
        assert(isinstance(other, StringValue))
        return other.descr in self.values

    def finalize(self):
        """Finalize the value"""
        # does nothing for now

    def _expandPerson(self):
        """Create all possible values for a person"""
        per = self.entity
        assert(per.tag == 'per')

        getAttr = lambda s: [v for x in per.attributes for v in x.values if x.name == s]

        firstnames = getAttr('firstname')
        lastnames = getAttr('lastname')
        patronymics = getAttr('patronymic')
        nicknames = getAttr('nickname')

        lists = [firstnames, lastnames, patronymics, nicknames]
        combinations = ['lfp', 'fpl', 'fp', 'fl', 'lf', 'n', 'f', 'p', 'l', 'fn']

        values = []
        for c in combinations:
            values += self._buildPerValues(lists, c)
        values.append(self.descr)
        self.values = set(values)

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

class SpanValue:
    """Fact argument that is a span"""

    def __init__(self, owner, full_id, descr, span_dict):
        """Initialize the object"""
        assert(full_id.startswith('span'))
        self.owner = owner
        self.span = span_dict[full_id[4:]]
        self.descr = descr.strip(' \n\r\t').lower()
        self.values = [self.descr]

    def __repr__(self):
        return self.descr

    def __str__(self):
        return self.__repr__()

    def equals(self, other):
        return other.value in self.values

    def finalize(self):
        """Finalize the value"""
        if self.owner.name == 'position':
            if(self.values[0] in Argument.position_dict):
                self.values.append(Argument.position_dict[self.values[0]])


class StringValue:
    """String value for special cases"""

    def __init__(self, value):
        """Initialie the object"""
        self.value = value.strip(' \n\r\t').lower()
        self.descr = self.value

    def __repr__(self):
        return self.descr

    def __str__(self):
        return self.descr

    def equals(self, other):
        # STUB
        return self.descr == other.descr

    def finalize(self):
        """Finalize the value"""
        # does nothing for now

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

        for alternative in alternatives:
            parts = alternative.split(' ')
            if parts[0].startswith('obj'):
                argument.values.append(
                    EntityValue(parts[0], ' '.join(parts[1:]), self.entity_dict))
            elif parts[0].startswith('span'):
                argument.values.append(
                    SpanValue(argument, parts[0], ' '.join(parts[1:]), self.span_dict))
            else:
                # just a string value
                argument.values.append(StringValue(alternative))

        return argument

class Fact:
    """Fact extracted from a document"""
    
    # values of the 'модальность' property that make the fact eligible for the easy mode
    # only
    easymode_modality_values = [
            'возможность',
            'будущее',
            'отрицание'
        ]

    # values of the 'сложность' property that make the fact eligible for the hard mode
    # only
    hardmode_difficulty_values = [
            'повышенная'
        ]

    def __init__(self):
        """Initialize the object (use Fact.fromStandard/Fact.fromTest instead)"""
        self.tag = ''
        self.arguments = []
        self.has_easymode_modality = False
        self.has_hardmode_difficulty = False
        self.is_ignored = False

    def __repr__(self):
        res = self.tag + '\n'
        for arg in self.arguments:
            res += str(arg) + '\n'

        return res

    def __str__(self):
        return repr(self)

    def toTestString(self):
        return '\n'.join([self.tag]
                         + [x.toTest() for x in self.arguments if not x.is_special]) + '\n'

    def toInlineString(self):
        res = '[ '
        if self.has_easymode_modality:
            res += '(MODALITY) '
        if self.has_hardmode_difficulty:
            res += '(HARD) '
        res += self.tag
        for arg in self.arguments:
            res += ' | {}'.format(arg)
        res += ' ]'
        return res

    # static build methods
    @classmethod
    def fromStandard(cls, text, entity_dict, span_dict):
        """"""
        assert(len(text.strip('\r\n\t ')) > 0)
        lines = text.split('\n')

        builder = ArgumentBuilder(entity_dict, span_dict)

        instance = cls()
        for line in lines[1:]:
            if len(line) == 0:
                continue
            arg = builder.build(line)
            arg.fact = instance
            instance.arguments.append(arg)

        # instance.processAttributes()
        instance._load_id_line(lines[0])
        instance.finalize()

        return instance

    @classmethod
    def fromTest(cls, text):
        """Load the entity from a test file using a different format:
        
        [fact_type]
        [arg_name]:[arg_value]
        ...
        [arg_name]:[arg_value]
        """

        assert(len(text.strip('\r\n\t ')) > 0)

        instance = cls()

        lines = text.split('\n')
        instance.tag = lines[0].strip(' :\n\t\r').lower()
        lines = text.split('\n')
        for line in lines[1:]:
            if len(line) == 0:
                continue
            arg = Argument.fromTest(line)
            arg.fact = instance
            instance.arguments.append(arg)

        return instance

    def _load_id_line(self, line):
        """Loads the first line of the fact description"""
        parts = line.split(' ')
        self.tag = parts[1].strip(' :\n\t\r').lower()

    def canMatch(self, other):
        """Determine if this fact can match the other in evaluation. In essense, returns
        True only if at least one of the arguments has matching values"""

        if self.tag != other.tag:
            return False

        for a in self.arguments:
            for b in other.arguments:
                # the following condition is a stub that prevents excessive matching
                if ((self.tag != 'occupation'
                            or a.name != 'position'
                                and a.name != 'where')
                        and a.canMatch(b)):
                    return True

        return False

    def removePhase(self):
        """Remove phase argument, it one is present"""
        phase_args = [a for a in self.arguments if a.name == 'фаза']
        if len(phase_args) == 0:
            return

        # there should be no more than one phase per fact
        assert(len(phase_args) == 1)
        self.arguments.remove(phase_args[0])

    def finalize(self):
        """Finalize the object for the evaluation"""
        self._processModality()
        self._processDifficulty()
        for arg in self.arguments:
            arg.finalize()

    def _processModality(self):
        modality_args = [a for a in self.arguments if a.name == 'модальность']
        if len(modality_args) == 0:
            self.has_easymode_modality = False
            return

        # there should be no more than one modality per fact
        assert(len(modality_args) == 1)
        modality = modality_args[0]
        self.arguments.remove(modality)

        assert(len(modality.values) == 1)

        assert(isinstance(modality.values[0], StringValue))
        value = modality.values[0].descr
        self.has_easymode_modality = value in Fact.easymode_modality_values

    def _processDifficulty(self):
        difficulty_args = [a for a in self.arguments if a.name == 'сложность']
        if len(difficulty_args) == 0:
            self.has_hardmode_difficulty = False
            return

        # there should be no more than one modality per fact
        assert(len(difficulty_args) == 1)
        difficulty = difficulty_args[0]
        self.arguments.remove(difficulty)

        assert(len(difficulty.values) == 1)

        assert(isinstance(difficulty.values[0], StringValue))
        value = difficulty.values[0].descr
        self.has_hardmode_difficulty = value in Fact.hardmode_difficulty_values

        