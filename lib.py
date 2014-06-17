#!/usr/bin/env python

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


def shutdown():
    print "exit"

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
