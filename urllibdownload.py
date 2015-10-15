#!/usr/bin/env python

import os
import urllib
import urllib2
import sys
import optparse
import operator
import re
import shutil
import time, datetime
from urlparse import urlparse

pygressbar = 1

try:
    from pygressbar.pygressbar import (RED,
                    COL_RESET,
                    BLUE, MAGENTA,
                    GREEN,
                    YELLOW,
                    CYAN,
                    WHITE)
    from pygressbar.pygressbar import (PygressBar,
                    SimpleProgressBar,
                    CustomProgressBar,
                    SimplePercentProgressBar,
                    SimpleAnimatedProgressBar,
                    SimpleColorBar)
except ImportError:
    pygressbar = None

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
     reporthook: report hook for urllib.urlretrieve.
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

def download_file(url, destfile):
    """
     download_file: function for download from url to save as destfile
        @url the source file to download.
        @destfile the destination save file for local.
    """
    file_url = url

    try:
        print("--> Downloading file: %s" % file_url)
        filename, msg = urllib.urlretrieve(
                #'http://code.jquery.com/jquery-2.1.1.js',
                file_url,
                reporthook = reporthook)

        print ""
        #print "File:", filename
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


def download_file_bar(url, destfile):
    """
     download_file_bar: function for download from url
            to save as destfile with progress bar.
        @url the source file to download.
        @destfile the destination save file for local.
    """
    file_url = url

    # Download the file
    if sys.version_info[0] == 3:
        f = urllib.request.urlopen(file_url)
    else:
        f = urllib.urlopen(file_url)

    # Get the total length of the file
    scale = int(f.headers["content-length"])
    chunk_size = 500
    try:
        length = int(os.environ['COLUMNS'])
    except (KeyError, ValueError):
        length = 80
    length -= 2

    bar = CustomProgressBar(length=length,
                            left_limit='[',
                            right_limit=']',
                            head_repr=None,
                            empty_repr=' ',
                            filled_repr='|',
                            start=0,
                            scale_start=0,
                            scale_end=scale)

    if os.path.exists(destfile):
        now = currenttime()
        tmpfile = "%s.%s" % (destfile, now)
        shutil.move(destfile, tmpfile)

    print("--> Downloading file: %s" % url)
    print_flag = 0
    with open(destfile, "wb+") as code:
        # Load all the data chunk by chunk
        while not bar.completed():
            data = f.read(chunk_size)
            code.write(data)
            bar.increase(chunk_size)

            # Don't print always
            if print_flag == 100:
                bar.show_progress_bar()
                print_flag = 0
            else:
                print_flag += 1

    bar.show_progress_bar()
    print("")
    print("%s finished :)" % url)

class SortedOptParser(optparse.OptionParser):
    '''Optparser which sorts the options by opt before outputting --help'''

    #FIXME: epilog parsing: OptionParser.format_epilog = lambda self, formatter: self.epilog

    def format_help(self, formatter=None, epilog=None):
        self.option_list.sort(key=operator.methodcaller('get_opt_string'))
        return optparse.OptionParser.format_help(self, formatter=None)

def expand_tilde(option, opt, value, parser):
    setattr(parser.values, option.dest, os.path.expanduser(value))

def parse_cmdline(argv):
    """Parses the command-line."""

    # get arguments
    parser = SortedOptParser(
            usage="Usage: %s -f filename -u url" % sys.argv[0],
            description='download url file use urllib.')
    parser.add_option('-o', '--output', dest='output', metavar='str',
                        help='file name for save.')
    parser.add_option('-u', '--url', dest='url', metavar='URL',
                        help='url file for download.')
    parser.add_option('-f', '--filelist', dest='filelist', metavar='FILE',
                        help='url file list for batch download.')
    parser.add_option('-d', '--dest', dest='dest', metavar='str',
                        action="callback", callback=expand_tilde,
                        default="./", help='dest dir for save file.')
    parser.add_option('-p', '--progress', action="store_true", default=False,
        dest='progress', help='disable progress bar fuction, default:enable.')
    (options, args) = parser.parse_args(args=argv[1:])

    if options.url is None and options.filelist is None:
        parser.print_usage()
        error_exit("option -u or -f is must.")

    if os.path.exists(options.dest):
        if not os.path.isdir(options.dest):
            parser.print_usage()
            error_exit("%s is not a dir." % options.dest)

        if not os.access(options.dest, os.W_OK | os.X_OK):
            error_exit("%s is not have a write priority." % options.dest)
    else:
        try:
            os.makedirs(options.dest)
        except os.error:
            error_exit("mkdir for %s catch exception." % options.dest)

    return (options, args)

def currenttime():
    """
     currenttime: function for return now time string.
    """
    nowtime = time.localtime()

    year = str(nowtime.tm_year)
    month = str(nowtime.tm_mon)
    if len(month) < 2:
        month = '0' + month
    day = str(nowtime.tm_mday)
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

def main(argv):
    """main program route."""
    options, args = parse_cmdline(argv)

    if options.filelist is not None:
        try:
            f_lists = open(options.filelist, "r")

            for line in f_lists:
                line = line.strip(' ').strip('\n\r')
                parsed = urlparse(line)
                filename = re.sub('[\\\/]', '', parsed.path)

                destfile = os.path.join(options.dest, filename)
                if pygressbar is None or options.progress:
                    download_file(line, destfile)
                else:
                    download_file_bar(line, destfile)
        finally:
            f_lists.close()
    else:
        if options.output is None:
            parsed = urlparse(options.url)
            options.output = re.sub('[\\\/]', '', parsed.path)

        destfile = os.path.join(options.dest, options.output)

        if pygressbar is None or options.progress:
            download_file(options.url, destfile)
        else:
            download_file_bar(options.url, destfile)

#########################################
# entry of program route.
#########################################
if __name__ == '__main__':
    sys.exit(main(sys.argv))

