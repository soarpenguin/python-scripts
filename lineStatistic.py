#!/usr/bin/env python

import sys
import re
import os
from optparse import OptionParser

prg_name = sys.argv[0]

RED   = "\x1b[31m"
GREEN = "\x1b[32m"
CYAN  = "\x1b[36m"
WHITE = "\x1b[37m"
YELLOW = "\x1b[33m"
BLUE   = "\x1b[34m"
MAGENTA = "\x1b[35m"
COL_RESET = "\x1b[0m"

def parse_cmdline(argv):
    """Parses the command-line."""

    # get arguments
    parser = OptionParser(
                usage='Usage: %s -f file' % prg_name,
                description='statistical script for file.')
    parser.add_option('-f', '--file', dest='file', metavar='str', help='file name for statistic.')
    (options, args) = parser.parse_args(args=argv[1:])

    if not options.file:
        parser.print_usage()
        error_exit("Must provide statistic filename, just like: %s -f filename"\
                % prg_name)

    return (options, args)

def error_exit(msg, status=1):
    #sys.stderr.write('Error: %s\n' % msg)
    err_msg = "%sError:%s %s\n" % (RED, COL_RESET, msg)
    sys.stderr.write(err_msg)
    sys.exit(status)

def message(msg):
    final_msg = "%s%s %s\n" % (BLUE, msg, COL_RESET)
    sys.stdout.write(final_msg)

map = {}

def main(argv):

    (options, args) = parse_cmdline(argv)

    try:
        f_file = open(options.file, "r")
    except IOError, e:
        error_exit("Open the file of \"%s\" failed." % options.file)

    for line in f_file:
        if line.strip() in map.keys():
             map[line.strip()] += 1
        else:
             map[line.strip()] = 1

    f_file.close()

    #for key in map.keys():
    #    print "%s: %d" % (key, map[key])
    array = map.items()
    total = 0
    array.sort(lambda (k1,v1),(k2,v2): cmp(v2,v1))
    for (key, value) in array:
        print("%s: %d" % (key, value))
        total += value

    message("+" * 50)
    message("all: %d" % total)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
