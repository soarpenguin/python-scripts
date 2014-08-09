#!/usr/bin/env python

import os
import urllib
import sys
import optparse
import re
import shutil
import time, datetime
from urlparse import urlparse

RED   = "\x1b[31m"
GREEN = "\x1b[32m"
CYAN  = "\x1b[36m"
WHITE = "\x1b[37m"
YELLOW = "\x1b[33m"
BLUE   = "\x1b[34m"
MAGENTA = "\x1b[35m"
COL_RESET = "\x1b[0m"

def reporthook(rblock, sblock, totalsize):
    """
     @totalsize is reported in bytes.
     @sblock is the amount read each time.
     @rblock is the number of blocks successfully read.
    """
    if not rblock:
        print 'Connect opened:'
        return

    if totalsize < 0:
        print 'Read %d blocks (%d bytes)' % (rblock, rblock * sblock)
    else:
        amountread = rblock * sblock
        print "Read %d blocks, or %d/%d" % (rblock, amountread, totalsize)

    return

def parse_cmdline(argv):
    """Parses the command-line."""

    # get arguments
    parser = optparse.OptionParser(
            usage="Usage: %s -f filename -u url" % sys.argv[0],
            description='download url file use urllib.')
    parser.add_option('-f', '--file', dest='file', metavar='str',
                        help='file name for save.')
    parser.add_option('-u', '--url', dest='url', metavar='str',
                        help='url file for download.')
    parser.add_option('-d', '--dest', dest='dest', metavar='str',
                        default="./", help='dest dir for save file.')
    (options, args) = parser.parse_args(args=argv[1:])

    if options.url is None:
        parser.print_usage()
        error_exit("option -u is must.")

    if os.path.exists(options.dest):
        if not os.path.isdir(options.dest):
            parser.print_usage()
            error_exit("%s is not a dir." % options.dest)
    else:
        try:
            os.makedirs(options.dest)
        except os.error:
            error_exit("mkdir for %s catch exception." % options.dest)

    return (options, args)

def currenttime(): 
    nowtime = time.localtime()

    year = str(nowtime.tm_year)
    month = str(nowtime.tm_mon)
    if len(month) < 2:
        month = '0' + month
    day =  str(nowtime.tm_yday)
    if len(day) < 2:
        day = '0' + day
    return (year + '-' + month + '-' + day)

def error_exit(msg, status=1):
    #sys.stderr.write('Error: %s\n' % msg)
    err_msg = "%sError:%s %s\n" % (RED, COL_RESET, msg) 
    sys.stderr.write(err_msg)
    sys.exit(status)

def message(msg):
    final_msg = "%s%s %s\n" % (BLUE, msg, COL_RESET)
    sys.stdout.write(final_msg)

"""main route for program."""
def main(argv):
    """main program route."""
    options, args = parse_cmdline(argv)

    if options.file is None:
        parsed = urlparse(options.url)
        options.file = re.sub('[\\\/]', '', parsed.path) 

    destfile = os.path.join(options.dest, options.file)

    try:
        filename, msg = urllib.urlretrieve(
                #'http://code.jquery.com/jquery-2.1.1.js',
                options.url,
                reporthook = reporthook)
    
        print ""
        print "File:", filename
        print "Header:"
        print msg
        if os.path.exists(filename):
            if os.path.exists(destfile):
                now = currenttime()
                tmpfile = "%s.%s" % (destfile, now)
                shutil.move(destfile, tmpfile)
            shutil.move(filename, destfile)

        #print 'File exists before cleanup:', os.path.exists(filename)
    finally:
        urllib.urlcleanup()
        #print 'File still exists:', os.path.exists(filename)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
