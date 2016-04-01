# Fact from the .facts layer of the standard markup

from dialent.objects.argument import Argument
from dialent.objects.argument import ArgumentBuilder

from dialent.objects.argument import StringValue
from dialent.objects.argument import EntityValue
from dialent.objects.argument import SpanValue

#########################################################################################

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
        self.id = ''
        self.arguments = []
        self.has_easymode_modality = False
        self.has_hardmode_difficulty = False
        self.is_ignored = False

    def toTestString(self):
        return '\n'.join([self.tag]
                         + [x.toTest() for x in self.arguments if not x.is_special]) + '\n'

    def toInlineString(self):
        res = '[ ' + str(self.id) + ' '
        if self.has_easymode_modality:
            res += '(MODALITY) '
        if self.has_hardmode_difficulty:
            res += '(HARD) '
        res += self.tag
        for arg in self.arguments:
            res += ' | {}'.format(arg)
        res += ' ]'
        return res

    def _load_id_line(self, line):
        """Loads the first line of the fact description"""
        parts = line.split(' ')
        self.id = parts[0]
        self.tag = parts[1].strip(' :\n\t\r').lower()

    def canMatch(self, other):
        """Determine if this fact can match the other in evaluation. In essense, returns
        True only if at least one of the arguments has matching values"""

        if self.tag != other.tag:
            return False

        for a in self.arguments:
            for b in other.arguments:
                if a.canMatch(b):
                   if a.name=='position':
                       continue
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

        # Apparently there can be multiple modality values in the dataset
        # And mutliple values per modality attribute
        for modality in modality_args:
            self.arguments.remove(modality)

            assert(isinstance(modality.values[0], StringValue))
            for value in modality.values:
                self.has_easymode_modality = (
                        self.has_easymode_modality
                        or (value.descr in Fact.easymode_modality_values)
                )

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

    def expandWithIsPartOf(self, facts):
        if self.tag != 'occupation':
            return

        partof_dict = {}
        for fact in facts:
            for arg in fact.arguments:
                for key in arg.values:
                    assert(isinstance(key, EntityValue))
                    for value in arg.values:
                        if value == key:
                            continue
                        if not (key in partof_dict):
                            partof_dict[key] = []
                        partof_dict[key].append(value)

        for arg in self.arguments:
            if arg.name == 'where':
                assert(len(arg.values) == 1)
                assert(isinstance(arg.values[0], EntityValue))
                arg.values[0].expandWithIsPartOf(partof_dict)

    def __repr__(self):
        res = self.tag + '\n'
        for arg in self.arguments:
            res += str(arg) + '\n'

        return res

    def __str__(self):
        return repr(self)

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

