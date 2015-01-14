# -*- coding: utf-8 -*-
"""
This is the configuration file, used by the main korp.cgi script.
"""

# The absolute path to the CQP binaries
CQP_EXECUTABLE = "/usr/local/cwb/bin/cqp"
CWB_SCAN_EXECUTABLE = "/usr/local/cwb/bin/cwb-scan-corpus"

# The absolute path to the CWB registry files
CWB_REGISTRY = "/v/corpora/registry"

# The default encoding for the cqp binary
# (this can be changed by the CGI parameter 'encoding')
CQP_ENCODING = "UTF-8"

# The maximum number of search results that can be returned per query (0 = no limit)
MAX_KWIC_ROWS = 0

# Number of threads to use during parallel processing
PARALLEL_THREADS = 3

# The name of the MySQL database and table prefix
DBNAME = "korp"
DBTABLE = "relations"
# Username and password for database access
DBUSER = "korp"
DBPASSWORD = ""

# Put PROTECTED_FILE contents, with PUB, ACA and RES, and other
# authorization information in the database (jpiitula Dec 2013)
AUTH_DBNAME = "korp_auth"
AUTH_DBUSER = "korp"
AUTH_DBPASSWORD = ""

# URL to authentication server
AUTH_SERVER = "http://localhost/cgi-bin/korp/auth.cgi"
# Secret string used when communicating with authentication server
AUTH_SECRET = ""

# A text file with names of corpora needing authentication, one per line
PROTECTED_FILE = "/v/corpora/protected.txt"

# Cache path (optional). Script must have read and write access. Cache needs to be cleared manually when corpus data is updated.
CACHE_DIR = "/v/korp/cache"

# Max number of rows from count command to cache
CACHE_MAX_STATS = 5000

# Whether corpora contain encoded special characters that would not
# otherwise be handled correctly (because of limitations of CWB):
# space, slash, lesser than, greater than. These characters are
# encoded in CQP queries and decoded in query results.
ENCODED_SPECIAL_CHARS = True
# Special characters encoded
SPECIAL_CHARS = u" /<>|"
# The character for encoding the first character in SPECIAL_CHARS. The
# characters used for encoding should not appear in the corpus as
# such, unless a multi-character encoding prefix is defined which does
# not appear in the corpus as such.
ENCODED_SPECIAL_CHAR_OFFSET = 0x7F
# Prefix for the encoded form of special characters. Note that a
# non-empty prefix means that a special character will not be matched
# by a single-character pattern in CQP regular expressions.
ENCODED_SPECIAL_CHAR_PREFIX = u""

# A text file with (regexps of) names of corpora whose sentences
# should never be displayed in corpus order, one per line
RESTRICTED_SENTENCES_CORPORA_FILE = "/v/corpora/restricted_sentences.txt"
# The default sorting order of the results for the above corpora (if
# no other order is specified)
RESTRICTED_SENTENCES_DEFAULT_SORT = "keyword"

import logging

# Path to log file; use /dev/null to disable logging
LOG_FILE = "/v/korp/log/korp-cgi.log"
# Log level: set to logging.DEBUG for also logging actual CQP
# commands, logging.WARNING for only warnings and errors,
# logging.CRITICAL to disable logging
LOG_LEVEL = logging.INFO

# Whether the corpora in the results should be sorted alphabetically;
# if not, the results are in the order specified by the form parameter
# "corpus".
SORT_CORPORA = False

# Whether the "info" command for corpora should retrieve extra
# information from the database table "corpus_info".
DB_HAS_CORPUSINFO = True