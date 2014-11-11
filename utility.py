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

join = os.path.join
py_version = 'python%s.%s' % (sys.version_info[0], sys.version_info[1])

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

if __name__ == '__main__':
    #configvalue = getConfig("./config.ini", "mysql", "port")
    #print configvalue

    print(check_access_rights(os.path.dirname(os.path.abspath(__file__))))
    setup_python_path("../")
#assert expression1, expression2
#if __debug__:
#    if not expression1: raise AssertionError(expression2)
