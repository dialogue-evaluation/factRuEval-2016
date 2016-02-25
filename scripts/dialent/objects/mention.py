# Representation of a span from the standard markup .spans layer

from dialent.config import Config

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
