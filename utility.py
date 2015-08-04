#!/usr/bin/env python
#-*-coding:utf-8-*-

import sys
import subprocess
import ConfigParser
import os
import optparse
import shutil
import re
from stat import S_ISDIR, S_ISREG, ST_MODE
import terminal
import pipes
import stat
import shlex
import select
import tempfile
import fcntl

try:
    import json
except ImportError:
    import simplejson as json

#import pdb
#pdb.set_trace()

join = os.path.join
py_version = 'python%s.%s' % (sys.version_info[0], sys.version_info[1])

def _import_localpath(path):
    import os
    if not os.path.isdir(path):
        print("[notice] import local path %s failed." % path)
        return 0

    sys.path.append(path)
    return 1

def _callable(obj):
    return hasattr(obj, '__call__') or hasattr(obj, '__bases__')

def _ensure_value(namespace, name, value):
    if getattr(namespace, name, None) is None:
        setattr(namespace, name, value)
    return getattr(namespace, name)

def mkdir(path):
    if not os.path.exists(path):
        print('Creating %s' % path)
        os.makedirs(path)
    else:
        if verbose:
            print('Directory %s already exists')

def symlink(src, dest):
    if not os.path.exists(dest):
        if verbose:
            print('Creating symlink %s' % dest)
        os.symlink(src, dest)
    else:
        print('Symlink %s already exists' % dest)


def rmtree(dir):
    if os.path.exists(dir):
        print('Deleting tree %s' % dir)
        shutil.rmtree(dir)
    else:
        if verbose:
            print('Do not need to delete %s; already gone' % dir)

def make_exe(fn):
    if os.name == 'posix':
        oldmode = os.stat(fn).st_mode & 07777
        newmode = (oldmode | 0555) & 07777
        os.chmod(fn, newmode)
        if verbose:
            print('Changed mode of %s to %s' % (fn, oct(newmode)))

def oops(msg):
    print(msg)
    sys.exit(1)

def msg(type, msg):
    if type=='step':
        head=''
    elif type=='download':
        head='\t'
    elif type=='prepare':
        head='\t'
    elif type=='cmd':
        head='\t\t'
    elif type=='finish':
        head='\t'
    else:
        head='@@@@@'
    print('[%f]%s%s' % (time.time(), head, msg))
    sys.stdout.flush()

def runcmd(cmd):
    ret = subprocess.Popen(cmd, shell=True,stdin=None,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE)
    stdout,stderr = ret.communicate()
    code = ret.wait()
    msg('cmd', 'CMD=[%s] ret=[%d]' % (cmd, code))
    if 0 == code:
        return True
    else:
        print(stdout, stderr)
        return False


def run_cmd(cmd, live=False, readsize=10):

    #readsize = 10
    cmdargs = shlex.split(cmd)
    p = subprocess.Popen(cmdargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout = ''
    stderr = ''
    rpipes = [p.stdout, p.stderr]
    while True:
        rfd, wfd, efd = select.select(rpipes, [], rpipes, 1)

        if p.stdout in rfd:
            dat = os.read(p.stdout.fileno(), readsize)
            if live:
                sys.stdout.write(dat)
            stdout += dat
            if dat == '':
                rpipes.remove(p.stdout)
        if p.stderr in rfd:
            dat = os.read(p.stderr.fileno(), readsize)
            stderr += dat
            if live:
                sys.stdout.write(dat)
            if dat == '':
                rpipes.remove(p.stderr)
        # only break out if we've emptied the pipes, or there is nothing to
        # read from and the process has finished.
        if (not rpipes or not rfd) and p.poll() is not None:
            break
        # Calling wait while there are still pipes to read can cause a lock
        elif not rpipes and p.poll() == None:
            p.wait()

    return p.returncode, stdout, stderr

def getConfig(file, group, configName):
    config = ConfigParser.ConfigParser()
    config.readfp(open(file, "rw"))
    configValue = config.get(group, configName.strip(' ').strip('\'').strip("\""))

    return configValue

def _print_message(self, message, file=None):
    if message:
        if file is None:
            file = _sys.stderr
        file.write(message)

def check_access_rights(top):
    for f in os.listdir(top):
        pathname = os.path.join(top, f)
        mode = os.stat(pathname).st_mode

        if S_ISDIR(mode):
            # directory, recurse into it
            check_access_rights(pathname)
        elif S_ISREG(mode):
            # file, check permissions
            re.match("0100775", oct(os.stat(pathname)[ST_MODE]))
        else:
            # unknown file type
            pass

def is_executable_file(path):
    """Checks that path is an executable regular file, or a symlink towards one.
    This is roughly ``os.path isfile(path) and os.access(path, os.X_OK)``.
    """
    # follow symlinks,
    fpath = os.path.realpath(path)

    if not os.path.isfile(fpath):
        # non-files (directories, fifo, etc.)
        return False

    mode = os.stat(fpath).st_mode

    if (sys.platform.startswith('sunos')
            and os.getuid() == 0):
        # When root on Solaris, os.X_OK is True for *all* files, irregardless
        # of their executability -- instead, any permission bit of any user,
        # group, or other is fine enough.
        #
        # (This may be true for other "Unix98" OS's such as HP-UX and AIX)
        return bool(mode & (stat.S_IXUSR |
                            stat.S_IXGRP |
                            stat.S_IXOTH))

    return os.access(fpath, os.X_OK)


def which(filename):
    '''This takes a given filename; tries to find it in the environment path;
    then checks if it is executable. This returns the full path to the filename
    if found and executable. Otherwise this returns None.'''

    # Special case where filename contains an explicit path.
    if os.path.dirname(filename) != '' and is_executable_file(filename):
        return filename
    if 'PATH' not in os.environ or os.environ['PATH'] == '':
        p = os.defpath
    else:
        p = os.environ['PATH']
    pathlist = p.split(os.pathsep)
    for path in pathlist:
        ff = os.path.join(path, filename)
        if is_executable_file(ff):
            return ff
    return None


def split_command_line(command_line):

    '''This splits a command line into a list of arguments. It splits arguments
    on spaces, but handles embedded quotes, doublequotes, and escaped
    characters. It's impossible to do this with a regular expression, so I
    wrote a little state machine to parse the command line. '''

    arg_list = []
    arg = ''

    # Constants to name the states we can be in.
    state_basic = 0
    state_esc = 1
    state_singlequote = 2
    state_doublequote = 3
    # The state when consuming whitespace between commands.
    state_whitespace = 4
    state = state_basic

    for c in command_line:
        if state == state_basic or state == state_whitespace:
            if c == '\\':
                # Escape the next character
                state = state_esc
            elif c == r"'":
                # Handle single quote
                state = state_singlequote
            elif c == r'"':
                # Handle double quote
                state = state_doublequote
            elif c.isspace():
                # Add arg to arg_list if we aren't in the middle of whitespace.
                if state == state_whitespace:
                    # Do nothing.
                    None
                else:
                    arg_list.append(arg)
                    arg = ''
                    state = state_whitespace
            else:
                arg = arg + c
                state = state_basic
        elif state == state_esc:
            arg = arg + c
            state = state_basic
        elif state == state_singlequote:
            if c == r"'":
                state = state_basic
            else:
                arg = arg + c
        elif state == state_doublequote:
            if c == r'"':
                state = state_basic
            else:
                arg = arg + c

    if arg != '':
        arg_list.append(arg)
    return arg_list


def copyfileobj(src, dst, length=None):
    """Copy length bytes from fileobj src to fileobj dst.
       If length is None, copy the entire content.
    """
    if length == 0:
        return
    if length is None:
        shutil.copyfileobj(src, dst)
        return

    BUFSIZE = 16 * 1024
    blocks, remainder = divmod(length, BUFSIZE)
    for b in range(blocks):
        buf = src.read(BUFSIZE)
        if len(buf) < BUFSIZE:
            raise OSError("end of file reached")
        dst.write(buf)

    if remainder != 0:
        buf = src.read(remainder)
        if len(buf) < remainder:
            raise OSError("end of file reached")
        dst.write(buf)
    return

def filemode(mode):
    """Deprecated in this location; use stat.filemode."""
    import warnings
    warnings.warn("deprecated in favor of stat.filemode",
                  DeprecationWarning, 2)
    return stat.filemode(mode)

def _safe_print(s):
    encoding = getattr(sys.stdout, 'encoding', None)
    if encoding is not None:
        s = s.encode(encoding, 'backslashreplace').decode(encoding)
    print(s + " ")

def setup_python_path(libdir):
    """Sets up PYTHONPATH so that collectors can easily import common code."""
    mydir = os.path.realpath(libdir)
    if not os.path.isdir(mydir):
        return
    pythonpath = os.environ.get('PYTHONPATH', '')
    if pythonpath:
        pythonpath += ':'
    pythonpath += mydir
    os.environ['PYTHONPATH'] = pythonpath

def shell_expand_path(path):
    ''' shell_expand_path is needed as os.path.expanduser does not work
        when path is None. '''
    if path:
        path = os.path.expanduser(os.path.expandvars(path))
    return path

# copied from utils, avoid circular reference fun :)
def mk_boolean(value):
    if value is None:
        return False
    val = str(value)
    if val.lower() in [ "true", "t", "y", "1", "yes" ]:
        return True
    else:
        return False

def is_quoted(data):
    return len(data) > 0 and (data[0] == '"' and data[-1] == '"' or data[0] == "'" and data[-1] == "'")

def unquote(data):
    ''' removes first and last quotes from a string, if the string starts and ends with the same quotes '''
    if is_quoted(data):
        return data[1:-1]
    return data

import fcntl
def buffer_input():
    origfl = fcntl.fcntl(sys.stdin.fileno(), fcntl.F_GETFL)
    fcntl.fcntl(sys.stdin.fileno(), fcntl.F_SETFL, origfl | os.O_NONBLOCK)
    try:
        stdin = sys.stdin.read()
    except IOError: # Stdin contained no information
        stdin = ""
    fcntl.fcntl(sys.stdin.fileno(), fcntl.F_SETFL, origfl)
    return stdin

def choose_one(choices, prompt):
    for idx, choice in enumerate(choices):
        print('%d. %s' % (idx + 1, choice))
    selected = None
    while not selected or selected <= 0 or selected > len(choices):
        selected = raw_input(prompt)
        try:
            selected = int(selected)
        except ValueError:
            selected = None
    return choices[selected - 1]

from types import *
from cStringIO import StringIO

def split_line(line, COLS=80, indent=10):
    indent = " " * indent
    width = COLS - (len(indent) + 1)
    if indent and width < 15:
        width = COLS - 2
        indent = " "
    s = StringIO()
    i = 0
    for word in line.split():
        if i == 0:
            s.write(indent+word)
            i = len(word)
            continue
        if i + len(word) >= width:
            s.write('\n'+indent+word)
            i = len(word)
            continue
        s.write(' '+word)
        i += len(word) + 1
    return s.getvalue()


def tar_create(path):
    if path:
        path = path.rstrip('/') or '/'
    else:
        path = '.'

    dirname = pipes.quote(os.path.dirname(path) or '.')
    basename = pipes.quote(os.path.basename(path) or '/')
    return 'tar c -C %s %s' % (dirname, basename)


def create_dir(path):
    """Creates a directory atomically."""

    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def process_checkpoint(program):
    '''
       this helper method checks if program is available in the sys
       if not fires up one
    '''
    try:
        cmd = "pgrep " + program
        subprocess.check_output(cmd, shell=True)
    except:
        # logger.warning('Your program is offline, will try to launch it now!', extra=extra_information)
        # close_fds = True argument is the flag that is responsible
        # for Popen to launch the process completely independent
        subprocess.Popen(program, close_fds=True, shell=True)
        time.sleep(3)

UNITS = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB']

def human_unit(size):
    """Return a string of the form '12.34 MiB' given a size in bytes."""
    for i in xrange(len(UNITS) - 1, 0, -1):
        base = 2.0 ** (10 * i)
        if 2 * base < size:
            return '%.2f %s' % ((float(size) / base), UNITS[i])
    return str(size) + ' ' + UNITS[0]

if sys.version_info[0] == 3:
    os.getcwdu = os.getcwd

def get_pwd():
    try:
        return os.getcwdu()
    except OSError:
        print("Current directory no longer exists.")
        raise

def is_number(s):
    try:
        float(s) # for int, long and float
    except ValueError:
        return False
    return True

import errno, os
def strerror(nr):
        try:
                return errno.errorcode[abs(nr)]
        except:
                return "Unknown %d errno" % nr

NSECS_PER_SEC    = 1000000000

def avg(total, n):
    return total / n

def nsecs(secs, nsecs):
    return secs * NSECS_PER_SEC + nsecs

def nsecs_secs(nsecs):
    return nsecs / NSECS_PER_SEC

def nsecs_nsecs(nsecs):
    return nsecs % NSECS_PER_SEC

def nsecs_str(nsecs):
    str = "%5u.%09u" % (nsecs_secs(nsecs), nsecs_nsecs(nsecs)),
    return str

import itertools
MAGIC_BRACKETS = re.compile('({([^}]+)})')
def expand_paths(path):
    """When given a path with brackets, expands it to return all permutations
       of the path with expanded brackets, similar to ant.
       >>> expand_paths('../{a,b}/{c,d}')
       ['../a/c', '../a/d', '../b/c', '../b/d']
       >>> expand_paths('../{a,b}/{a,b}.py')
       ['../a/a.py', '../a/b.py', '../b/a.py', '../b/b.py']
       >>> expand_paths('../{a,b,c}/{a,b,c}')
       ['../a/a', '../a/b', '../a/c', '../b/a', '../b/b', '../b/c', '../c/a', '../c/b', '../c/c']
       >>> expand_paths('test')
       ['test']
       >>> expand_paths('')
    """
    pr = itertools.product
    parts = MAGIC_BRACKETS.findall(path)

    if not path:
        return

    if not parts:
        return [path]

    permutations = [[(p[0], i, 1) for i in p[1].split(',')] for p in parts]
    return [_replace_all(path, i) for i in pr(*permutations)]

def _replace_all(path, replacements):
    for j in replacements:
        path = path.replace(*j)
    return path


def hexbitmask(l, nr_entries):
    hexbitmask = []
    bit = 0
    mask = 0
    for entry in range(nr_entries):
        if entry in l:
            mask |= (1 << bit)
        bit += 1
        if bit == 32:
            bit = 0
            hexbitmask.insert(0, mask)
            mask = 0

    if bit < 32 and mask != 0:
        hexbitmask.insert(0, mask)

    return hexbitmask

def to_safe(word):
    """ Converts 'bad' characters in a string to underscores. """

    return re.sub("[^A-Za-z0-9\-]", "_", word)

def json_format_dict(data, pretty=False):
    """ Converts a dict to a JSON object and dumps it as a formatted string """

    if pretty:
        return json.dumps(data, sort_keys=True, indent=2)
    else:
        return json.dumps(data)

def jsonify(result, format=False):
    ''' format JSON output (uncompressed or uncompressed) '''

    if result is None:
        return "{}"
    result2 = result.copy()
    for key, value in result2.items():
        if type(value) is str:
            result2[key] = value.decode('utf-8', 'ignore')

    indent = None
    if format:
        indent = 4

    try:
        return json.dumps(result2, sort_keys=True, indent=indent, ensure_ascii=False)
    except UnicodeDecodeError:
        return json.dumps(result2, sort_keys=True, indent=indent)

def log_lockfile(prog):
    # create the path for the lockfile and open it
    tempdir = tempfile.gettempdir()
    uid = os.getuid()
    path = os.path.join(tempdir, "%s.lock.%s" % (prig, uid))
    lockfile = open(path, 'w')
    # use fcntl to set FD_CLOEXEC on the file descriptor,
    # so that we don't leak the file descriptor later
    lockfile_fd = lockfile.fileno()
    old_flags = fcntl.fcntl(lockfile_fd, fcntl.F_GETFD)
    fcntl.fcntl(lockfile_fd, fcntl.F_SETFD, old_flags | fcntl.FD_CLOEXEC)
    return lockfile

def last_non_blank_line(buf):

    all_lines = buf.splitlines()
    all_lines.reverse()
    for line in all_lines:
        if (len(line) > 0):
            return line
    # shouldn't occur unless there's no output
    return ""

def rst_fmt(text, fmt):
    ''' helper for Jinja2 to do format strings '''

    return fmt % (text)

def rst_xline(width, char="="):
    ''' return a restructured text line of a given length '''

    return char * width


if __name__ == '__main__':
    #configvalue = getConfig("./config.ini", "mysql", "port")
    #print configvalue
    paths = expand_paths('../{a,b,c}/{a,b,c}')
    print paths

    print(check_access_rights(os.path.dirname(os.path.abspath(__file__))))
    setup_python_path("../")

    _import_localpath("../")
    print sys.path

    print terminal.terminal_size()
    print human_unit(12400000)
    process_checkpoint("mysqld")
#assert expression1, expression2
#if __debug__:
#    if not expression1: raise AssertionError(expression2)


