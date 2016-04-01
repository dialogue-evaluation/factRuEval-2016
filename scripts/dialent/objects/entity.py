# Entity from the .coref layer of the standard markup

#########################################################################################

from dialent.objects.attribute import Attribute

class Entity:
    """Entity with a set of attributes, assembled from several mentions throughout the
    document"""


    def __init__(self):
        """Create a new object. Do not call this directly, use classmethods instead."""
        self.attributes = []
        self.id = -1
        self.tag = 'unknown'
        self.spans = []
        self.mentions = []
        self.is_problematic = False


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
                if name == 'name':
                    # extend names with qoutes if available
                    added_attrs = [x.tryPutInQoutes(self) for x in attr_by_name]
                    attr_by_name.extend(x for x in added_attrs if x != None)
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
        res += ' ' + str(self.id) if self.id != -1 else ''
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


    def getAttr(self, name):
        """Return all values of the attribute with a given name"""
        return [v for attr in self.attributes for v in attr.values if attr.name == name]

    def __repr__(self):
        res = ''
        res += '{} #{}'.format(self.tag, self.id)
        for attribute in self.attributes:
            res += '\n  {}'.format(attribute)
        return res


    def __str__(self):
        return self.__repr__()


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
        instance.processAttributes()

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
        instance.tag = lines[0].lower().strip(' :\r\n\t')
        if instance.tag == 'locorg':
            # all locorgs are considered locs for this task
            instance.tag = 'loc'

        return instance

