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
import atexit
import fcntl
import time

NUMREGX = re.compile(r'^(-{0,1}|\+{0,1})[0-9]+(\.{0,1}[0-9]+)$')


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
    result=""
    if not NUMREGX.match(str(seconds)):
        return result

    day = float(seconds) / ((24 * 60 * 60))
    hour = float(seconds) / (60 * 60) % 24
    minuter = float(seconds) / 60 % 60

    if day > 1:
        result += "%d days, " % day
    else: 
        result += "%d day, " % day

    if hour > 0:
        result += "%02d:%02d" % (hour, minuter)
    else:
        result += "%02d min" % min

    return result


def fmtshare(share, pagesize):
    """ format share size """
    if ( not NUMREGX.match(str(seconds)) ) or ( not NUMREGX.match(str(pagesize)) ):
        return "?"

    share = int(share) * (int(pagesize) >> 10)
    result = ""

    if (int(share) <= 9999):
        result = "%d" % share
    elif (int(share) <= 2 << 20):
        result = "%dm" % (int(share) >> 10)
    elif (int(share) <= 2 << 30):
        result = "%dg" % (int(share) >> 20)
    else:
        result = "?"

    return result


def get_all_process():
    """ get all process id from /proc. """

    PROC = "/proc"
    process = list()
    try:
        process = os.listdir(PROC)

        process = [elem for elem in process if str(elem).isdigit() ]
    except:
        return list()

    return process


def get_sys_loads():
    """ get sys loads from /proc/loadavg. """

    LOADAVG = "/proc/loadavg"
    loadavg = list()
    try:
        f_loadavg = open(LOADAVG, "r")
    except IOError, e:
        return loadavg

    f_loadavg.seek(0)
    loadavg = f_loadavg.readline().split(None)[0:3]

    f_loadavg.close()
    return loadavg


def get_memswap_info():
    """ get memory and swap infomation from /proc/meminfo. """

    MEMINFO = "/proc/meminfo"
    meminfo = list()
    pattern = re.compile(r'MemTotal|MemFree|Buffers|Cached|SwapTotal|SwapFree')

    try:
        f_meminfo = open(MEMINFO, "r")
    except IOError, e:
        return meminfo

    f_meminfo.seek(0)
    for line in f_meminfo:
        m = pattern.match(line)
        if m:
            meminfo.append(line.split(None)[1])

    f_meminfo.close()
    return meminfo


def scale_num(num, width, pagesize):
    """ format number to fit width. """

    num = int(num) * (int(pagesize) >> 10)
    result = "?"

    if (int(num) <= (10 ** int(width) - 1)):
        result = "%d" % num
    elif (int(num) <= 1024 * 1024):
        result = "%dm" % (int(num) / 1024)
    elif (int(num) <= 1024 * 1024 * 1024):
        result = "%dg" % (int(num) / (1024 * 1024))

    return result


def fmt_mem_percent(mem, memtotal, pagesize):
    """ format memory num to percent. """

    result = "0"
    if NUMREGX.match(str(mem)) and NUMREGX.match(str(memtotal)):
        result = "%.1f" % (int(mem)*int(pagesize)/1024*100/int(memtotal))

    return result


def set_fd_nonblocking(fd):
    """ set fd nonblocking. """

    if not fd:
        return -1

    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)


def usage():
    usage = """
Help for Interactive Commands - $script version $myversion
Window 1:Def: Cumulative mode Off.  System: Delay 3.0 secs; Secure mode Off.

  Z,B       Global: 'Z' change color mappings; 'B' disable/enable bold
  l,t,m     Toggle Summaries: 'l' load avg; 't' task/cpu stats; 'm' mem info
  1,I       Toggle SMP view: '1' single/separate states; 'I' Irix/Solaris mode

  f,o     . Fields/Columns: 'f' add or remove; 'o' change display order
  F or O  . Select sort field
  <,>     . Move sort field: '<' next col left; '>' next col right
  R,H     . Toggle: 'R' normal/reverse sort; 'H' show threads
  c,i,S   . Toggle: 'c' cmd name/line; 'i' idle tasks; 'S' cumulative time
  x,y     . Toggle highlights: 'x' sort field; 'y' running tasks
  z,b     . Toggle: 'z' color/mono; 'b' bold/reverse (only if 'x' or 'y')
  u       . Show specific user only
  n or #  . Set maximum tasks displayed

  k,r       Manipulate tasks: 'k' kill; 'r' renice
  d or s    Set update interval
  W         Write configuration file
  q         Quit
          ( commands shown with '.' require a visible task display window ) 
Press 'h' or '?' for help with Windows,
any other key to continue """
    return usage


def header():
    now = time.strftime("%H:%M:%S", time.localtime()) 
    uptime = read_uptime()[0]
    #uptime = fmttime(read_uptime()[0])
    (sysload1, sysload5, sysload15) = get_sys_loads()
    head = "%5s - %8s up %5s, %2d users,  load average: %3s, %3s, %3s\n" % ("top.py", now, fmttime(uptime), 3, sysload1, sysload5, sysload15)
    ## $uptime
    return head


def main(argv):
    """ The main top entry point and loop."""

    options, args = parse_cmdline(argv)
    #clrscr()
    size = getpagesize()
    #print size
    #print fmttime(3600)
    cpus = get_cpu_info()
    #for elem in cpus:
    #    for key in elem.keys():
    #        print "%s => %s" % (key, elem.get(key))
    #print get_all_process()
    #print get_sys_loads()
    #print get_memswap_info()
    #print scale_num(1024, 4, size)
    #print fmt_mem_percent(1024, 4096, size)
    #usage()
    #set_fd_nonblocking(sys.stdout)
    try:
        screen = curses.initscr()
        atexit.register(curses.endwin)

        curses.noecho()
        curses.curs_set(0)
        screen.keypad(1)
        #curses.cbreak()
        #screen.clear()
        screen.addstr(0, 0, "screen", curses.A_BLINK)

        height,width=screen.getmaxyx()
        screen.addstr(height - 1, 0, "position string", curses.A_BLINK)

        while True:
            event = screen.getch()
            if event == ord("q"): 
                break
            elif event == ord("h") or event == ord("?"):
                screen.addstr(0, 0, usage())
                screen.refresh()
            #else:
                #screen.clear()
            screen.addstr(0, 0, header())

        curses.nocbreak()
        screen.keypad(0)
        curses.echo()
    except:
        curses.nocbreak()
        if screen:
            screen.keypad(0)
        curses.echo()
        traceback.print_exc() 
    finally:
        curses.endwin()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
