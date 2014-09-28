#!/usr/bin/env python
#-*-coding:utf-8-*-

import sys
import subprocess
import ConfigParser
import os
import optparse
import shutil

join = os.path.join
py_version = 'python%s.%s' % (sys.version_info[0], sys.version_info[1])

def mkdir(path):
    if not os.path.exists(path):
        print 'Creating %s' % path
        os.makedirs(path)
    else:
        if verbose:
            print 'Directory %s already exists'

def symlink(src, dest):
    if not os.path.exists(dest):
        if verbose:
            print 'Creating symlink %s' % dest
        os.symlink(src, dest)
    else:
        print 'Symlink %s already exists' % dest


def rmtree(dir):
    if os.path.exists(dir):
        print 'Deleting tree %s' % dir
        shutil.rmtree(dir)
    else:
        if verbose:
            print 'Do not need to delete %s; already gone' % dir

def make_exe(fn):
    if os.name == 'posix':
        oldmode = os.stat(fn).st_mode & 07777
        newmode = (oldmode | 0555) & 07777
        os.chmod(fn, newmode)
        if verbose:
            print 'Changed mode of %s to %s' % (fn, oct(newmode))

def oops(msg):
    print msg
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
    print '[%f]%s%s' % (time.time(), head, msg)
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
        print stdout, stderr
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

if __name__ == '__main__':
    configvalue = getConfig("./config.ini", "mysql", "port")
    print configvalue
#assert expression1, expression2
#if __debug__:
#    if not expression1: raise AssertionError(expression2)
