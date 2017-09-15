#!/usr/bin/python
# -*- coding: utf-8 -*-


import time
import cgi
import json
import MySQLdb
import korp_config as config


# The name of the MySQL database and table prefix
DBTABLE = "lemgram_index"


def main():
    starttime = time.time()
    print_header()

    # Convert form fields to regular dictionary
    form_raw = cgi.FieldStorage()
    form = dict((field, form_raw.getvalue(field)) for field in form_raw.keys())

    wf = form.get("wf")
    corpora = form.get("corpus")
    limit = int(form.get("limit", 10))
    if corpora:
        corpora = corpora.split(',')
    result = {}
    try:
        result["div"] = get_lemgrams(wf, corpora, limit)
        result["count"] = len(result["div"])
        result["time"] = time.time() - starttime
        result["s"] = repr(result)
        print_object(result, form)
    except:
        import traceback, sys
        exc = sys.exc_info()
        error = {"ERROR": {"type": exc[0].__name__,
                           "value": str(exc[1]),
                           "traceback": traceback.format_exc().splitlines(),
                           },
                 "time": time.time() - starttime}
        print_object(error, form)


def get_lemgrams(wf, corpora, limit):
    conn = MySQLdb.connect(use_unicode=True,
                           charset="utf8",
                           **config.DBCONNECT)
    # Get Unicode objects even with collation utf8_bin; see
    # <http://stackoverflow.com/questions/9522413/mysql-python-collation-issue-how-to-force-unicode-datatype>
    conn.converter[MySQLdb.constants.FIELD_TYPE.VAR_STRING] = [
        (None, conn.string_decoder)]
    cursor = conn.cursor()
    result = query_lemgrams(cursor, wf, corpora, limit)[:limit]
    cursor.close()
    conn.close()
    return encode_lemgram_result(result)


def query_lemgrams(cursor, wf, corpora, limit):
    result = []
    sql = make_lemgram_query(wf, corpora, limit)
    cursor.execute(sql)
    # Note: Checking and filtering the results returned from the
    # database is probably not needed when using collation utf8_bin,
    # since it is case-sensitive and does not collate "har", "hår" and
    # "här". Using a case-insensitive collation such as
    # utf8_swedish_ci or utf8_unicode_ci would not use the index,
    # since the collation for the table is utf8_bin, so it would be
    # unacceptably slow. Case-insensitive matching would probably
    # require a separate column with preprocessed (lowercased, perhaps
    # accents removed) lemgrams, since apparently MySQL/MariaDB does
    # not support specifying indexes with different collations.
    modcase = (lambda w: w.lower()) if wf.islower() else (lambda w: w)
    for row in cursor:
        if modcase(row[0].encode("utf-8")).startswith(wf):
            result.append(row[0])
    return result


def make_lemgram_query(wf, corpora, limit):
    sql = make_lemgram_query_corpora(wf, corpora, limit)
    if corpora:
        sql += ' union ' + make_lemgram_query_corpora(wf, [], limit)
    return sql + ';'


def make_lemgram_query_corpora(wf, corpora, limit):
    return ' union '.join([make_lemgram_query_part(wf + suffpatt, corpora, limit)
                           for suffpatt in ['..%', '%']])


def make_lemgram_query_part(pattern, corpora, limit):
    return ("(select distinct lemgram from lemgram_index where lemgram like '"
            + pattern + "'"
            + (" and corpus in (" + ','.join(["'" + corp + "'"
                                             for corp in corpora]) + ")"
               if corpora else '')
            # This would be too slow:
            # + " collate 'utf8_swedish_ci'"
            + " order by lemgram"
            + " limit " + str(limit)
            + ")")


def encode_lemgram_result(lemgrams):
    return [{"class": ["entry"],
             "div": {"class": "source",
                     "resource": "lemgram_index"},
             "LexicalEntry": {"lem": lemgram}}
            for lemgram in lemgrams]


def print_header():
    """Prints the JSON header."""
    print "Content-Type: application/json"
    print "Access-Control-Allow-Origin: *"
    print


def print_object(obj, form):
    """Prints an object in JSON format.
    The CGI form can contain optional parameters 'callback' and 'indent'
    which change the output format.
    """
    callback = form.get("callback")
    if callback: print callback + "(",
    try:
        indent = int(form.get("indent"))
        print json.dumps(obj, sort_keys=True, indent=indent),
    except:
        print json.dumps(obj, separators=(",",":"))
    if callback: print ")",
    print


if __name__ == "__main__":
    main()
