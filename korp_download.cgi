#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
A CGI script to export Korp search results to downloadable formats.

The script uses modules in the korpexport package to do most of the
work.

The following CGI (query string) parameters are recognized and used by
the script. If run from the command-line, the parameters are given as
a single command-line argument, encoded as in a URL.

Parameters:
    query_params (JSON): `korp.cgi` parameters format for generating a
        query result; if specified, `korp.cgi` is called to generate
        the result
    query_result (JSON): The Korp query result to format; overrides
        `query_params`
    format (string): The format to which to convert the result;
        default: ``json`` (JSON)
    filename_format (string): A format specification for the
        (suggested) name of the file to generate; may contain the
        following format keys: ``cqpwords``, ``start``, ``end``,
        ``date``, ``time``, ``ext``; default:
        ``korp_kwic_{cqpwords}_{date}_{time}.{ext}``
    filename (string): The (suggested) name of the file to generate;
        overrides `filename_format`
    korp_server (URL): The Korp server to query; default configured in
       code
    logfile (string): The name of the file to which to write log
        messages; default configured in code; use /dev/null to disable
        logging
    debug (boolean): If specified, write debug messages to the log
        file
    
The script requires at least one of the parameters `query_params` and
`query_result` to make the search result for downloading.

Additional parameters are recognized by formatter modules.

To write a formatter for a new format, add a corresponding module to
the package `korpexport.format`. Please see
:mod:`korpexport.formatter` for more information.

If the script is invoked directly from the command line (not via CGI),
the it outputs log messages to standard error by default. This can be
changed by specifying the parameter `logfile`.

:Author: Jyrki Niemi <jyrki.niemi@helsinki.fi> for FIN-CLARIN
:Date: 2014
"""


from __future__ import absolute_import

import sys
import os
import os.path
import time
import cgi
import logging
import urllib

import korpexport.exporter as ke


# Default Korp server URL
# The URL does not work with restricted corpora but the script name
# does
# KORP_SERVER = "http://localhost/cgi-bin/korp/korp.cgi"
KORP_SERVER = os.path.join(os.path.dirname(__file__), "korp.cgi")

# Path to log file; use /dev/null to disable logging
LOG_FILE = "/v/korp/log/korp-cgi.log"
# Log level: set to logging.DEBUG for also logging actual CQP
# commands, logging.WARNING for only warnings and errors,
# logging.CRITICAL to disable logging
LOG_LEVEL = logging.INFO


def main():
    """The main CGI handler, modified from that of korp.cgi.

    Converts CGI parameters to a dictionary and initializes logging.
    Invokes :func:`korpexport.exporter.make_download_file` to generate
    downloadable content.
    """
    starttime = time.time()
    # Open unbuffered stdout
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
    # Convert form fields to regular dictionary with unicode values;
    # assume that the input is encoded in UTF-8. Note that this does
    # not handle list values resulting form multiple occurrences of a
    # parameter.
    form_raw = cgi.FieldStorage(keep_blank_values=1)
    form = dict((field, form_raw.getvalue(field).decode("utf-8"))
                for field in form_raw.keys())
    # Configure logging
    loglevel = logging.DEBUG if "debug" in form else LOG_LEVEL
    logfile = form.get("logfile")
    if 'GATEWAY_INTERFACE' in os.environ:
        # The script is run via CGI
        logfile = logfile or LOG_FILE
    # If the script is run on the command line (not via CGI) and the
    # parameter logfile is not specified, write log messages to stderr
    logging_config_filearg = (dict(filename=logfile) if logfile
                              else dict(stream=sys.stderr))
    logging.basicConfig(format=('[%(filename)s %(process)d' +
                                ' %(levelname)s @ %(asctime)s]' +
                                ' %(message)s'),
                        level=loglevel,
                        **logging_config_filearg)
    # Log remote IP address and CGI parameters
    logging.info('IP: %s', cgi.os.environ.get('REMOTE_ADDR'))
    # Limit the length of query_result written to the log
    logging.info("Params: {'format': '%s', 'filename': '%s', "
                 "'query_params': '%s', 'query_result': '%.800s', "
                 "'headings': '%s', 'structs': '%s', 'attrs': '%s'}",
                 form.get("format"), form.get("filename"),
                 form.get("query_params"), form.get("query_result"),
                 form.get("headings"), form.get("structs"), form.get("attrs"))
    try:
        result = ke.make_download_file(form, 
                                       form.get("korp_server", KORP_SERVER))
    except Exception as e:
        import traceback
        exc = sys.exc_info()
        result = {"ERROR": {"type": exc[0].__name__,
                            "value": str(exc[1])}
                  }
        result["ERROR"]["traceback"] = traceback.format_exc().splitlines()
        logging.error("%s", result["ERROR"])
        # Show traceback only if the parameter debug is specified
        if "debug" not in form:
            del result["ERROR"]["traceback"]
    # Print HTTP header and content
    print_header(result)
    print_object(result)
    # Log elapsed time
    logging.info("Elapsed: %s", str(time.time() - starttime))


def print_header(obj):
    """Print HTTP header for the downloadable file (or error message).

    Arguments:
        obj (dict): The downloadable file contents and information
            about it (or an error message); may contain the following
            keys that affect the output headers:

            - download_content_type => Content-Type (default:
              ``text/plain``)
            - download_charset => Charset (default: utf-8)
            - download_filename => Content-Disposition filename
            - download_content => Length of the content to
              Content-Length

            If `obj` contains the key ``ERROR``, output
            ``text/plain``, not an attachment.
    """
    charset = obj.get("download_charset")
    print ("Content-Type: "
           + (obj.get("download_content_type", "text/plain")
              if "ERROR" not in obj
              else "text/plain")
           + (("; charset=" + charset) if charset else ""))
    if "ERROR" not in obj:
        # Default filename 
        print make_content_disposition_attachment(
            obj.get("download_filename", "korp_kwic"))
        print "Content-Length: " + str(len(obj["download_content"]))
    print


def make_content_disposition_attachment(filename):
    """Make a HTTP Content-Disposition header with attachment filename.

    Arguments:
        filename (str): The file name to use for the attachment

    Returns:
        str: A HTTP ``Content-Disposition`` header for an attachment
            with a parameter `filename` with a value `filename`

    If `filename` contains non-ASCII characters, encode it in UTF-8 as
    specified in RFC 5987 to the `Content-Disposition` header
    parameter `filename*`, as showin in a `Stackoverflow discussion`_.
    For a wider browser support, also provide a `filename` parameter
    with the encoded filename. According to the discussion, this does
    not work with IE prior to version 9 and Android browsers.
    Moreover, at least Firefox 28 on Linux seems save an empty file
    with the corresponding Latin-1 character in its name, in addition
    to the real file.

    .. _Stackoverflow discussion: http://stackoverflow.com/questions/93551/how-to-encode-the-filename-parameter-of-content-disposition-header-in-http
    """
    filename = urllib.quote(filename)
    return (("Content-Disposition: attachment; "
             + ("filename*=UTF-8''{filename}; " if "%" in filename else "")
             + "filename={filename}")
            .format(filename=filename))


def print_object(obj):
    """Print the downloadable content or an error message.

    Arguments:
        obj (dict): The downloadable content (in key
            `download_content`) or an error message dict in `ERROR`.
    """
    if "ERROR" in obj:
        error = obj["ERROR"]
        print "Error when trying to download results:"
        print error["type"] + ": " + error["value"]
        if "traceback" in error:
            print error["traceback"]
    else:
        print obj["download_content"],


if __name__ == "__main__":
    main()
