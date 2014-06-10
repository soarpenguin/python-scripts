#!/usr/bin/env python

# top.py -- top command implemented use python.
#    get infomation from /proc system.
#    the main file for system info is:
#      /proc/stat /proc/<pid>/status /proc/<pid>/stam etc.

import sys
import re
import os
from optparse import OptionParser
from terminal import *
import curses, traceback


def read_uptime():
    try:
        f_uptime = open("/proc/uptime", "r")
        line = f_uptime.readline()

        return line.split(None)
    finally:
        f_uptime.close()


def get_system_hz():
    """Return system hz use SC_CLK_TCK."""
    ticks = os.sysconf(os.sysconf_names['SC_CLK_TCK'])

    if ticks == -1:
        return 100
    else:
        return ticks


def parse_cmdline(argv):
    """Parses the command-line."""

    # get arguments
    parser = OptionParser(description='Top command script for display system '
                          'infomation.')
    parser.add_option('-d', '--delay', dest='delay', metavar='int', default=3,
                      help='Delay time interval: -d ss.tt(second.tenths).')
    parser.add_option('-n', '--number', dest='number',
                      metavar='int', default=0,
                      help='Number of interations limit ad: -n number')
    parser.add_option('-u', '--user', dest='user', metavar="str",
                      default="all", help='Monitor only processes with an ' 
                      'effective UID or user name.')
    parser.add_option('-v', dest='verbose', action='store_true', default=False,
                      help='Display version information.')
    (options, args) = parser.parse_args(args=argv[1:])

    return (options, args)


def getpagesize():
    """ get the system pagesize from /proc/self/smaps """

    SMAPS = "/proc/self/smaps"
    size = 4
    unit = "kB"
    pattern = re.compile(r'KernelPageSize|MMUPageSize')

    if os.path.exists(SMAPS):
        try:
            f_smaps = open(SMAPS, "r")

            for line in f_smaps:
                m = pattern.match(line)
                if m:
                    array = re.split("\s+", line)
                    size = array[1]
                    unit = array[2]
                    break
        finally:
            f_smaps.close()

    if re.match("kB", unit):
        size = int(size) * 1024
    elif re.match("mB", unit):
        size = int(size) * 1024 * 1024
    elif re.match("gB", unit):
        size = int(size) * 1024 * 1024 * 1024

    return size


CPU_T = (
    "u", "s", "n", "i", "w"        
)
def get_cpu_info():
    """get cpus infomation from /proc/stat """

    cpus = list()
    cpustat = "/proc/stat"
    try:
        f_stat = open(cpustat, "r")
    except IOError, e:
        return cpus

    f_stat.seek(0)
    for line in f_stat:
        if re.match("cpu", line):
            values = line.split(None)
            cpu = dict(zip(CPU_T, values[1:]))
            cpus.append(cpu)

    f_stat.close()
    return cpus


def fmttime(seconds):
    """ format seconds to string like: '12days, 01:12' """
    tmpstring=""
    if not str(seconds).isdigit():
        return tmpstring

    day = int(seconds) / ((24 * 60 * 60))
    hour = int(seconds) / (60 * 60) % 24
    minuter = int(seconds) / 60 % 60

    if day > 1:
        tmpstring += "%s days, " % day
    else: 
        tmpstring += "%s day, " % day

    if hour > 0:
        tmpstring += "%02d:%02d" % (hour, minuter)
    else:
        tmpstring += "%02d min" % min

    return tmpstring


def main(argv):
    """ The main top entry point and loop."""

    options, args = parse_cmdline(argv)
    #clrscr()
    size = getpagesize()
    print size
    print fmttime(3600)
    cpus = get_cpu_info()
    #for elem in cpus:
    #    for key in elem.keys():
    #        print "%s => %s" % (key, elem.get(key))
    try:
        curses.initscr()
        screen=curses.newwin(80, 74, 0, 0)
        screen.box()
        #curses.noecho()
        curses.cbreak()
        screen.keypad(1)
        #screen.clear()
        height,width=screen.getmaxyx()
        screen.addstr(0, 0, "jjjjjjjjjj", curses.A_BLINK)
        screen.refresh()

        curses.nocbreak()
        screen.keypad(0)
        curses.echo()
    except:
        curses.nocbreak()
        screen.keypad(0)
        curses.echo()
        traceback.print_exc() 
    finally:
        curses.endwin()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
