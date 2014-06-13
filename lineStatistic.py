#!/usr/bin/env python

import sys
import re
import os
from optparse import OptionParser


def parse_cmdline(argv):
    """Parses the command-line."""

    # get arguments
    parser = OptionParser(description='statistical script for file.')
    parser.add_option('-f', '--file', dest='file', metavar='str', help='file name for statistic.')
    (options, args) = parser.parse_args(args=argv[1:])

    return (options, args)

map = {}

def main(argv):

    (options, args) = parse_cmdline(argv)

    if not options.file:
        print("must provide statistic filename.")
        sys.exit(1)

    try:
        f_file = open(options.file, "r")
    except IOError, e:
        sys.exit(1)

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
        print "%s: %d" % (key, value)
        total += value

    print "++++++++++++++++"
    print "all: %d" % total


if __name__ == '__main__':
    sys.exit(main(sys.argv))
