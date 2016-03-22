# Representation of a span from the standard markup .spans layer

from dialent.config import Config
from dialent.config import Tables

from dialent.objects.interval import Interval
from dialent.objects.tokenset import TokenSet

#########################################################################################

class Mention:
    """Mention consisting of spans"""
    
    def __init__(self, id, tag, span_ids, span_dict):
        """Create a new mention of a given type with the provided spans"""
        self.id = id
        self.parents = []
        
        if not tag in Config.STANDARD_TYPES:
            raise Exception('Unknown mention tag: {}'.format(tag))
        self.tag = Config.STANDARD_TYPES[tag]
        
        self.spans = []
        self.text = ''
        self.interval_text = ''
        for id in span_ids:
            self.spans.append(span_dict[id])
        
    def __repr__(self):
        res = '{} #{}:\n'.format(self.tag, self.id)
        for span in self.spans:
            res += '\t{} : {}\n'.format(span.tag, span.text)
        res += '\n'
        return res

    def isGeoAdj(self):
        """Checks if the mention only has geo_adj spans"""
        non_geo_adj = [s for s in self.spans if s.tag != 'geo_adj']
        return len(non_geo_adj) == 0

    def isDescr(self):
        """Checks if the mention only has descriptor spans"""
        non_descr = [s for s in self.spans if 'descr' not in s.tag]
        return len(non_descr) == 0

    def findParents(self, mentions):
        """Scans the given mention list for mentions embedding this one"""
        self.parents = []
        for m in [x for x in mentions if x.tag in Tables.PARENT_TAGS[self.tag]]:
            s_int = self.toInterval()
            m_int = m.toInterval()
            if s_int.isIn(m_int):
                self.parents.append(m)
            else:
                # organizations have priority over equally sized people and locations
                if self.tag in ['per', 'loc'] and m.tag=='org' and s_int.isEqual(m_int):
                    self.parents.append(m)

    def toInterval(self):
        assert(len(self.spans) > 0)
        by_start = sorted(self.spans, key=lambda x: x.start)
        by_end = sorted(self.spans, key=lambda x: x.end)
        start = by_start[0].start
        length = by_end[-1].end - by_start[0].start + 1
        return Interval(start, length)

    def setText(self, documentText):
        """Sets the text from the document corresponding to the mention"""
        ts = TokenSet([t for s in self.spans for t in s.tokens], self.tag, documentText)
        self.text = ' '.join([t.text for t in ts.sortedTokens()])
        interval = ts.toInterval()
        self.interval_text = documentText[interval.start:interval.end]

    def __str__(self):
        return repr(self)
