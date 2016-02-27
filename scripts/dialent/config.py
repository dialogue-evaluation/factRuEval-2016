# This module contains various settings and global parameters

#########################################################################################

class Config:
    """Global configuration"""
    DEFAULT_DELIMITER = ' '
    QUOTECHAR = '|'
    TOKEN_LINE_LENGTH = 4
    SPAN_FILE_SEPARATOR = '  # '
    COMMENT_SEPARATOR = '#'
    STANDARD_TYPES = {
        'Person' : 'per',
        'Organization' : 'org',
        'Org' : 'org',
        'LocOrg' : 'locorg',
        'Location' : 'loc',
        'Project' : 'project'
    }
    
#########################################################################################

class Tables:
    """Tables with error weights"""

    def getMark(mention_tag, span_tag, dfl_value = 0):
        """Lookup error weight of the provided pair.
        
        Returns default value if the pair is not in QUALITY table"""
        if mention_tag in Tables.QUALITY and span_tag in Tables.QUALITY[mention_tag]:
            return Tables.QUALITY[mention_tag][span_tag]
        else:
            return dfl_value

    def getArgumentWeight(tag):
        """Lookup the given argument weight"""

        if tag in Tables.ARG_WEIGHTS:
            return Tables.ARG_WEIGHTS[tag]
        else:
            return 1.0

    ARG_WEIGHTS = {
        'position' : 0.5,
        'фаза' : 0.5
        }

    # this table specifies weights of various spans in mention evaluation
    QUALITY = {
        'locorg' : {
            'none' : 1,
#            'loc_descr' : 1,
            'org_name' : 1,
#            'org_descr' : 1,
#            'loc_descr' : 1,
            'loc_name' : 1
        },

        'loc' : {
            'none' : 1,
#            'name' : 1,
#            'org_descr' : 1,
            'org_name' : 1,
#            'loc_descr' : 1,
#            'surname' : 1,
            'loc_name' : 1,
#            'nickname' : 1
        },

        'org' : {
            'none' : 1,
#            'org_descr' : 1,
#            'surname' : 1,
            'loc_name' : 1,
#            'loc_descr' : 1,
            'org_name' : 1,
#            'job' : 1
        },

        'per' : {
            'none' : 1,
            'name' : 1,
            'patronymic' : 1,
            'nickname' : 1,
            'surname' : 1
        }
    }

    # This table describes rules for mention and tokenset embedding, e.g.
    # mentions with tag KEY can be embedded in mentions with tag VALUE
    PARENT_TAGS = {
        'per' : ['loc', 'org', 'locorg'],
        'loc' : ['loc', 'org', 'locorg'],
        'org' : ['org', 'locorg'],
        'locorg' : ['org', 'locorg'],
        'project' : ['org', 'locorg']
    }
