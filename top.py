#!/usr/bin/env python
# -*- coding: utf-8 -*-

# top.py -- top command implemented use python.
#    get infomation from /proc system.
#    the main file for system info is:
#      /proc/stat /proc/<pid>/status /proc/<pid>/stam etc.

from __future__ import print_function
import sys
import re
import os
from optparse import OptionParser
from terminal import *
import traceback
import atexit
import fcntl
import time
import signal

try:
    import curses, _curses
except ImportError:
    print("Curse is not available on this system. Exiting.", file=sys.stderr)
    sys.exit(0)

NUMREGX = re.compile(r'^(-{0,1}|\+{0,1})[0-9]+(\.{0,1}[0-9]+)$')
CONFIGURATION = {
        'pause_refresh': False,
        'refresh_interval': 3.0,
        'help_mode': False,
}


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


PROC_T = (
    "pid", "cmd", "state", "ppid", "pgrp", "session", "tty", "tpgid", "flags",
    "min_flt", "cmin_flt", "maj_flt", "cmaj_flt", "utime", "stime", "cutime",
    "cstime", "priority", "nice", "timeout", "it_real_value", "start_time",
    "vsize", "rss", "rss_rlim", "start_code", "end_code", "start_stack",
    "kstk_esp", "kstk_eip", "signal", "blocked", "sigignore", "sigcatch",
    "wchan", "nswap", "cnswap", "exit_signal", "processor", "rtprio", "sched",
    "ruid", "euid", "suid", "fuid", "rgid", "egid", "sgid", "fgid", "vm_size",
    "vm_lock", "vm_rss", "vm_data", "vm_stack", "vm_exe", "vm_lib"
)
def get_process_stat(proc_id):
    """ get process stat from /proc/#/stat. """
    import pwd
    import grp

    proc_t = {}
    if not str(proc_id).isdigit() or\
       not os.path.exists("/proc/" + proc_id):
        return proc_t

    STAT = "/proc/" + proc_id + "/stat"
    try:
        f_stat = open(STAT, "r")
        stats = f_stat.readline().split(None)
        proc_t = dict(zip(PROC_T, stats[0:]))
        proc_t["cmd"] = re.sub('[()]', '', proc_t["cmd"])

        if int(proc_t["tty"]) == 0:
            proc_t["tty"] = -1
        if int(proc_t["priority"]) < 0:
            proc_t["priority"] = "RT"
        proc_t["pcpu"] = int(proc_t["utime"]) + int(proc_t["stime"])
        proc_t["tics"] = int(proc_t["utime"]) + int(proc_t["stime"])
    except IOError, e:
        return proc_t
    finally:
        f_stat.close()

    STATUS = "/proc/" + proc_id + "/status"
    try:
        f_status = open(STATUS, "r")
        for line in f_status:
            if re.match("uid:", line, re.I):
                (proc_t["ruid"],proc_t["euid"],proc_t["suid"],proc_t["fuid"])\
                    = line.split(None)[1:]
            elif re.match("Gid:", line, re.I):
                (proc_t["rgid"],proc_t["egid"],proc_t["sgid"],proc_t["fgid"])\
                    = line.split(None)[1:]
            elif re.match("VmSize:", line, re.I):
                (proc_t["vm_size"]) = line.split(None)[1]
            elif re.match("VmLck", line, re.I):
                (proc_t["vm_lock"]) = line.split(None)[1]
            elif re.match("VmRss", line, re.I):
                (proc_t["vm_rss"]) = line.split(None)[1]
            elif re.match("VmData:", line, re.I):
                (proc_t["vm_data"]) = line.split(None)[1]
            elif re.match("VmStk:", line, re.I):
                (proc_t["vm_stack"]) = line.split(None)[1]
            elif re.match("VmExe:", line, re.I):
                (proc_t["vm_exe"]) = line.split(None)[1]
            elif re.match("VmLib:", line, re.I):
                (proc_t["vm_lib"]) = line.split(None)[1]
    except IOError, e:
        return proc_t
    finally:
        f_status.close()
    proc_t["euser"] = pwd.getpwuid(int(proc_t["euid"]))[0]
    proc_t["ruser"] = pwd.getpwuid(int(proc_t["ruid"]))[0]
    proc_t["suser"] = pwd.getpwuid(int(proc_t["suid"]))[0]
    proc_t["egroup"] = grp.getgrgid(int(proc_t["egid"]))[0]
    proc_t["rgroup"] = grp.getgrgid(int(proc_t["rgid"]))[0]
    proc_t["fgroup"] = grp.getgrgid(int(proc_t["fgid"]))[0]
    if proc_t["state"] == "Z":
        proc_t["cmd"] += " <defunct>"

    STATM = "/proc/" + proc_id + "/statm"
    try:
        f_statm = open(STATM, "r")
        (proc_t["size"],proc_t["resident"],proc_t["share"],\
         proc_t["trs"],proc_t["lrs"],proc_t["drs"],proc_t["dt"])\
           = f_statm.readline().split(None)
    except IOError, e:
        return proc_t
    finally:
        f_statm.close()

    CMDLINE = "/proc/" + proc_id + "/cmdline"
    try:
        f_cmdline = open(CMDLINE, "r")
        proc_t["cmdline"] = f_cmdline.readline()
    except IOError, e:
        return proc_t
    finally:
        f_cmdline.close()

    ENVIRON = "/proc/" + proc_id + "/environ"
    try:
        f_environ = open(ENVIRON, "r")
        proc_t["environ"] = f_environ.readline()
    except IOError, e:
        return proc_t

    return proc_t


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
    if ( not NUMREGX.match(str(seconds)) )\
            or ( not NUMREGX.match(str(pagesize)) ):
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


def get_all_user():
    """ get user of system """
    import pwd

    all_user = {}
    for user in pwd.getpwall():
        all_user[user[0]] = all_user[user[2]] = user

    return all_user


def usage():
    usage = """
Help for Interactive Commands - top.py version 1.0.0.0
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


def header(processes, memory):
    """ return string of top header. """

    now = time.strftime("%H:%M:%S", time.localtime())
    uptime = read_uptime()[0]
    #uptime = fmttime(read_uptime()[0])
    (sysload1, sysload5, sysload15) = get_sys_loads()

    total = len(processes)
    running = 0; sleeping = 0; stoped = 0; zombie = 0;

    cpus = get_cpu_info()
    us = float(cpus[0].get("u"))
    sy = float(cpus[0].get("s"))
    ni = float(cpus[0].get("n"))
    idle = float(cpus[0].get("i"))
    wa = float(cpus[0].get("w"))
    summary = us + sy + ni + idle + wa
    scale = 100.0 / summary

    (memtotal, memfree, buf, cache, swaptotal, swapfree) = memory[0:]
    memused = int(memtotal) - int(memfree)
    swapused = int(swaptotal) - int(swapfree)

    head = "%5s - %8s up %5s, %2d users,  load average: %3s, %3s, %3s\n" \
        % ("top.py", now, fmttime(uptime), 3, sysload1, sysload5, sysload15)
    head = head + "Tasks: %3d total,   %2d running, %3d sleeping, %3d stopped, %2d zombie\n" \
        % (total, running, sleeping, stoped, zombie)
    head = head + "Cpu(s):  %2.1f%%us, %2.1f%%sy, %2.1f%%ni, %2.1f%%id, %2.1f%%wa, 0.0%%hi, 0.0%%si, 0.0%%st\n" \
        % (us*scale, sy*scale, ni*scale, idle*scale, wa*scale)
    head = head + "Mem:  %8sk total, %8sk used, %8sk free, %8sk buffers\n" \
        % (memtotal, memused, memfree, buf)
    head = head + "Swap: %8sk total, %8sk used, %8sk free, %8sk cached\n" \
        % (swaptotal, swapused, swapfree, cache)

    return head

def on_keyboard(scr, c):
    '''Handle keyborad shortcuts'''
    if c == ord('q'):
        raise KeyboardInterrupt()
    elif c == ord('p'):
        CONFIGURATION['pause_refresh'] = not CONFIGURATION['pause_refresh']
    elif c == ord('h') or c == ord('?'):
        CONFIGURATION['pause_refresh'] = not CONFIGURATION['pause_refresh']
        display(scr, usage(), False)
        return 1

    return 1

def on_mouse():
    '''Update selected line / sort'''
    _, x, y, z, bstate =  curses.getmouse()

    # Left button click ?
    if bstate & curses.BUTTON1_CLICKED:
        # Is it title line ?
        if y == 0:
            # Determine sort column based on offset / col width
            x_max = 0
            return 2
        # Is it a cgroup line ?
    return 1

def on_resize():
    '''Redraw screen, do not refresh'''
    return 2

def event_listener(scr, timeout):
    '''
    Wait for curses events on screen ``scr`` at mot ``timeout`` ms

    return
     - 1 OK
     - 2 redraw
     - 0 error
    '''
    try:
        scr.timeout(timeout)
        c = scr.getch()
        if c == -1:
            return 1
        elif c == curses.KEY_MOUSE:
            return on_mouse()
        elif c == curses.KEY_RESIZE:
            return on_resize()
        else:
            return on_keyboard(scr, c)
    except _curses.error:
        return 0

def do_finish():
    """ Stop top.py and reinit curses."""
    curses.nocbreak()
    stdscr.keypad(0)
    curses.echo()
    curses.endwin()

    #The end...
    sys.exit(0)

def signal_handler():
    """Callback for CTRL-C."""
    do_finish()

class Timer(object):
    """The timer class. A simple chronometer."""

    def __init__(self, duration):
        self.duration = duration
        self.start()

    def start(self):
        self.target = time() + self.duration

    def reset(self):
        self.start()

    def set(self, duration):
        self.duration = duration

    def finished(self):
        return time() > self.target

def init_screen():
    curses.start_color() # load colors
    curses.use_default_colors()
    curses.noecho()      # do not echo text
    curses.cbreak()      # do not wait for "enter"
    curses.mousemask(curses.ALL_MOUSE_EVENTS)

    # Hide cursor, if terminal AND curse supports it
    if hasattr(curses, 'curs_set'):
        try:
            curses.curs_set(0)
        except:
            pass

def display(scr, info, head=False):
    # Get display informations
    height, width = scr.getmaxyx()
    list_height = height - 5 # title + status lines

    # Display statistics
    scr.clear()

    scr.addstr(0, 0, info)
    #scr.addstr(5, 0, "\n")

    if head:
        title = "  PID USER      PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND"
        scr.addstr(6, 0, ' '*width, curses.color_pair(2))
        scr.addstr(6, 0, title, curses.color_pair(2))

    scr.refresh()


def main(argv):
    """ The main top entry point and loop."""

    options, args = parse_cmdline(argv)
    CONFIGURATION['refresh_interval'] = float(options.delay)

    try:
        screen = curses.initscr()
        init_screen()
        atexit.register(curses.endwin)
        screen.keypad(1)     # parse keypad control sequences

        # Curses colors
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN) # header
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)  # focused header / line
        curses.init_pair(3, curses.COLOR_WHITE, -1)  # regular
        curses.init_pair(4, curses.COLOR_CYAN,  -1)  # tree

        #height,width = screen.getmaxyx()
        #signal.signal(signal.SIGINT, signal_handler)
        #screen.addstr(height - 1, 0, "position string", curses.A_BLINK)

        while True:
            #screen.timeout(0)
            processes = get_all_process()
            memory = get_memswap_info()
            display(screen, header(processes, memory), True)

            sleep_start = time.time()
            #while CONFIGURATION['pause_refresh'] or time.time() < sleep_start + CONFIGURATION['refresh_interval']:
            while CONFIGURATION['pause_refresh'] or time.time() < sleep_start + CONFIGURATION['refresh_interval']:
                if CONFIGURATION['pause_refresh']:
                    to_sleep = -1
                else:
                    to_sleep = int((sleep_start + CONFIGURATION['refresh_interval'] - time.time())*1000)

                ret = event_listener(screen, to_sleep)
                if ret == 2:
                    display(screen, header(processes, memory), True)

    except KeyboardInterrupt:
        pass
    finally:
        do_finish()

if __name__ == '__main__':
    sys.exit(main(sys.argv))
