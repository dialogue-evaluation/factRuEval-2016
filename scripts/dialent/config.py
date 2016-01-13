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
        'Location' : 'loc'
    }
    
#########################################################################################

class Tables:
    """Tables with error weights"""

    def getMark(entity_tag, span_tag, dfl_value = 0):
        """Lookup error weight of the provided pair.
        
        Returns default value if the pair is not in QUALITY table"""
        if entity_tag in Tables.QUALITY and span_tag in Tables.QUALITY[entity_tag]:
            return Tables.QUALITY[entity_tag][span_tag]
        else:
            return dfl_value


    # this table specifies weights of various spans in entity evaluation
    QUALITY = {
        'locorg' : {
#            'none' : 1,
#            'loc_descr' : 1,
            'org_name' : 1,
#            'org_descr' : 1,
#            'loc_descr' : 1,
            'loc_name' : 1
        },

        'loc' : {
#            'none' : 1,
#            'name' : 1,
#            'org_descr' : 1,
#            'org_name' : 1,
#            'loc_descr' : 1,
#            'surname' : 1,
            'loc_name' : 1,
#            'nickname' : 1
        },

        'org' : {
#            'none' : 1,
#            'org_descr' : 1,
#            'surname' : 1,
#            'loc_name' : 1,
#            'loc_descr' : 1,
            'org_name' : 1,
#            'job' : 1
        },

        'per' : {
#            'none' : 1,
            'name' : 1,
            'patronymic' : 1,
            'nickname' : 1,
            'surname' : 1
        }
    }
