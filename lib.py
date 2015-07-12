#!/usr/bin/env python

from __future__ import division
import string
import re
import os
import pwd
import types
import sys
from sys import stderr
import stat
import errno
import time
import subprocess
import threading
import struct
import socket
import textwrap


import os.path
path = os.path.realpath(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(path)))

try:
    import queue
except ImportError: # Python 2
    import Queue as queue


class ListenGetch(threading.Thread):

    def __init__(self, nom=''):
        threading.Thread.__init__(self)
        self.Terminated = False
        self.q = queue.Queue()

    def run(self):
        while not self.Terminated:
            char = msvcrt.getch()
            self.q.put(char)

    def stop(self):
        self.Terminated = True
        while not self.q.empty():
            self.q.get()

    def get(self, default=None):
        try:
            return ord(self.q.get_nowait())
        except Exception:
            return default


def _parse_args(args):
    dargs = {
        'Version':3,
        'DestHost':'localhost',
        'Community':'public',
        'Timeout':1000000,
        'Retries':3,
        'RemotePort':161,
        'LocalPort':0
        }
    keys = args.keys()
    for key in keys:
        if dargs.has_key(key):
            dargs[key] = args[key]
        else:
            print >>sys.stderr, "ERROR: unknown key", key
    return dargs

def STR(obj):
    if obj != None:
        obj = str(obj)
    return obj

class VarList(object):
    def __init__(self, *vs):
        self.varbinds = []

        for var in vs:
            self.varbinds.append(var)

    def __len__(self):
        return len(self.varbinds)

    def __getitem__(self, index):
        return self.varbinds[index]

    def __setitem__(self, index, val):
            self.varbinds[index] = val

    def __iter__(self):
        return iter(self.varbinds)

    def __delitem__(self, index):
        del self.varbinds[index]

    def __repr__(self):
        return repr(self.varbinds)

    def __getslice__(self, i, j):
        return self.varbinds[i:j]

    def append(self, *vars):
         for var in vars:
                self.varbinds.append(var)

def drop_privileges(user="nobody"):
    try:
        ent = pwd.getpwnam(user)
    except KeyError:
        return

    if os.getuid() != 0:
        return

    print >>stderr, "drop privilege."
    os.setgid(ent.pw_gid)
    os.setuid(ent.pw_uid)

def is_sockfile(path):
    """Returns whether or not the given path is a socket file."""
    try:
        s = os.stat(path)
    except OSError, (no, e):
        if no == errno.ENOENT:
            return False
        print >>sys.stderr, ("warning: couldn't stat(%r): %s" % (path, e))
        return None
    return s.st_mode & stat.S_IFSOCK == stat.S_IFSOCK

def is_numeric(value):
    return isinstance(value, (int, long, float))

NUMBER_RE = re.compile(
    r'(-?(?:0|[1-9]\d*))(\.\d+)?([eE][-+]?\d+)?',
    (re.VERBOSE | re.MULTILINE | re.DOTALL))

SYNTAX_GROUP_REGEX = re.compile(
  r"""^
      (?P<group_name>\w+)
      \s+
      xxx
      \s+
      (?P<content>.+?)
      $""",
  re.VERBOSE )

KEYWORD_REGEX = re.compile( r'^[\w,]+$' )

SYNTAX_ARGUMENT_REGEX = re.compile(
  r"^\w+=.*$" )

ROOT_GROUPS = set([
  'Statement',
  'Boolean',
  'Include',
  'Type',
])
#for root_group in ROOT_GROUPS:
#    print root_group

def read_file(fpath):
    BLOCK_SIZE = 1024
    with open(fpath, 'rb') as f:
        while True:
            block = f.read(BLOCK_SIZE)
            if block:
                yield block
            else:
                return

# next bit filched from 1.5.2's inspect.py
def currentframe():
   """Return the frame object for the caller's stack frame."""
   try:
       raise Exception
   except:
       return sys.exc_info()[2].tb_frame.f_back

IDENTIFIER = re.compile('^[a-z_][a-z0-9_]*$', re.I);

def valid_ident(s):
    m = IDENTIFIER.match(s)
    if not m:
        raise ValueError("Not a valid Python identifier: %r" % s)
    return True

def _repr(self):
    return "<%s at 0x%x: %s>" % (self.__class__.__name__, id(self), self)

def _parse_num(val, type):
    if val[:2].lower() == "0x":         # hexadecimal
        radix = 16
    elif val[:2].lower() == "0b":       # binary
        radix = 2
        val = val[2:] or "0"            # have to remove "0b" prefix
    elif val[:1] == "0":                # octal
        radix = 8
    else:                               # decimal
        radix = 10

    return type(val, radix)

def _parse_int(val):
    return _parse_num(val, int)

#######################################################
def _floatconstants():
    _BYTES = '7FF80000000000007FF0000000000000'.decode('hex')
    if sys.byteorder != 'big':
        _BYTES = _BYTES[:8][::-1] + _BYTES[8:][::-1]
    nan, inf = struct.unpack('dd', _BYTES)
    return nan, inf, -inf

NaN, PosInf, NegInf = _floatconstants()


def linecol(doc, pos):
    lineno = doc.count('\n', 0, pos) + 1
    if lineno == 1:
        colno = pos + 1
    else:
        colno = pos - doc.rindex('\n', 0, pos)
    return lineno, colno


class colors_enabled:
    red = '\033[31m'
    green = '\033[32m'
    yellow = '\033[33m'
    blue = '\033[34m'
    cyan = '\033[36m'
    bright_green = '\033[92m'

    bold = '\033[1m'
    faint = '\033[2m'

    end = '\033[0m'


def errmsg(msg, doc, pos, end=None):
    # Note that this function is called from _json
    lineno, colno = linecol(doc, pos)
    if end is None:
        fmt = '{0}: line {1} column {2} (char {3})'
        return fmt.format(msg, lineno, colno, pos)
        #fmt = '%s: line %d column %d (char %d)'
        #return fmt % (msg, lineno, colno, pos)
    endlineno, endcolno = linecol(doc, end)
    fmt = '{0}: line {1} column {2} - line {3} column {4} (char {5} - {6})'
    return fmt.format(msg, lineno, colno, endlineno, endcolno, pos, end)
    #fmt = '%s: line %d column %d - line %d column %d (char %d - %d)'
    #return fmt % (msg, lineno, colno, endlineno, endcolno, pos, end)


def error_exit(msg, status=1):
    sys.stderr.write('Error: %s\n' % msg)
    sys.exit(status)

def error_textwrap(self, msg, status, wrap_text=True):
    if wrap_text:
        new_msg = "\n[ERROR]: %s" % msg
        wrapped = textwrap.wrap(new_msg, 79)
        new_msg = "\n".join(wrapped) + "\n"
    else:
        new_msg = msg

    sys.stderr.write(new_msg)
    sys.exit(status)

def shutdown():
    print "exit"


def exec_cmd(cmd_list, retry_times=1, retry_interval_sec=0):
    ret = 0
    output = None

    cmd.extend(cmd_list)
    #cmd.append("--cluster=%s" % cluster_id)

    while retry_times > 0:
        try:
            output = subprocess.check_output(cmd)
            output = output.rstrip()
            break
        except subprocess.CalledProcessError, er:
            ret = er.returncode
            output = None
            retry_times -= 1
            if retry_interval_sec > 0: time.sleep(retry_interval_sec)

    return (ret, output)


USE_SHELL = sys.platform.startswith("win")
def exec_cmd_with_stderr(command,
                         universal_newlines = True,
                         useshell = USE_SHELL,
                         env = os.environ):
    try:
        p = subprocess.Popen(command,
                          stdout = subprocess.PIPE,
                          stderr = subprocess.PIPE,
                          shell = useshell,
                          universal_newlines = universal_newlines,
                          env = env)
        output = p.stdout.read()
        p.wait()
        errout = p.stderr.read()
        p.stdout.close()
        p.stderr.close()
        return p.returncode, output, errout
    except :
        return -1, None, None


def unique(old_list):
    new_list = []
    for x in old_list:
        if x not in new_list :
            new_list.append(x)
    return new_list

import cStringIO, traceback
#ei = sys.exc_info()
def formatException(ei):
    """
    Format and return the specified exception information as a string.

    This default implementation just uses
    traceback.print_exception()
    """
    sio = cStringIO.StringIO()
    traceback.print_exception(ei[0], ei[1], ei[2], None, sio)
    s = sio.getvalue()
    sio.close()
    if s[-1:] == "\n":
        s = s[:-1]
    return s

def humanize_bytes(n, precision=2):
    # Author: Doug Latornell
    # Licence: MIT
    # URL: http://code.activestate.com/recipes/577081/
    """Return a humanized string representation of a number of bytes.

    Assumes `from __future__ import division`.

    >>> humanize_bytes(1)
    '1 B'
    >>> humanize_bytes(1024, precision=1)
    '1.0 kB'
    >>> humanize_bytes(1024 * 123, precision=1)
    '123.0 kB'
    >>> humanize_bytes(1024 * 12342, precision=1)
    '12.1 MB'
    >>> humanize_bytes(1024 * 12342, precision=2)
    '12.05 MB'
    >>> humanize_bytes(1024 * 1234, precision=2)
    '1.21 MB'
    >>> humanize_bytes(1024 * 1234 * 1111, precision=2)
    '1.31 GB'
    >>> humanize_bytes(1024 * 1234 * 1111, precision=1)
    '1.3 GB'

    """
    abbrevs = [
        (1 << 50, 'PB'),
        (1 << 40, 'TB'),
        (1 << 30, 'GB'),
        (1 << 20, 'MB'),
        (1 << 10, 'kB'),
        (1, 'B')
    ]

    if n == 1:
        return '1 B'

    for factor, suffix in abbrevs:
        if n >= factor:
            break

    # noinspection PyUnboundLocalVariable
    return '%.*f %s' % (precision, n / factor, suffix)


# Python 2.x?
is_py2 = (sys.version_info[0] == 2)
# Python 3.x?
is_py3 = (sys.version_info[0] == 3)

def dict_to_sequence(d):
    """Returns an internal sequence dictionary update."""
    if hasattr(d, 'items'):
        d = d.items()

    return d

def to_native_string(string, encoding='ascii'):
    """
        Given a string object, regardless of type, returns a representation of that
        string in the native string type, encoding and decoding where necessary.
        This assumes ASCII unless told otherwise.
    """
    out = None
    if isinstance(string, builtin_str):
        out = string
    else:
        if is_py2:
            out = string.encode(encoding)
        else:
            out = string.decode(encoding)
    return out

def get_file_content(path, default=None, strip=True):
    data = default
    if os.path.exists(path) and os.access(path, os.R_OK):
        try:
            datafile = open(path)
            data = datafile.read()
            if strip:
                data = data.strip()
            if len(data) == 0:
                data = default
        finally:
            datafile.close()
    return data

def get_file_lines(path):
    '''file.readlines() that closes the file'''
    datafile = open(path)
    try:
        return datafile.readlines()
    finally:
        datafile.close()

def Array(typecode, sequence, lock=True):
    return array.array(typecode, sequence)

class Value(object):
    def __init__(self, typecode, value, lock=True):
        self._typecode = typecode
        self._value = value
    def _get(self):
        return self._value
    def _set(self, value):
        self._value = value
    value = property(_get, _set)
    def __repr__(self):
        return '<%r(%r, %r)>'%(type(self).__name__,self._typecode,self._value)


def enable_sig_handler(signal_name, handler):
    '''
    Add signal handler for signal name if it exists on given platform
    '''
    if hasattr(signal, signal_name):
        signal.signal(getattr(signal, signal_name), handler)

if __name__ == '__main__':
    var_list = VarList()
    var_list.append("name")
    print >>stderr, STR(var_list)

    drop_privileges()

    print is_sockfile(sys.argv[0])

    #for i in open("lib.py"):
    #    print i

    import atexit
    atexit.register(shutdown)

    print valid_ident("_fedl")

    _repr(var_list)
    #while True:
    #    time.sleep(1)

    import platform
    if sys.platform.startswith('linux'):
        sys.stderr.write('linux\n')
    elif sys.platform == 'darwin' and platform.processor() == 'i386':
        sys.stderr.write('darwin\n')
    elif os.name == 'nt':
        sys.stderr.write('nt\n')
    else:
        sys.stderr.write('not found\n')

    print _parse_int("02345")

