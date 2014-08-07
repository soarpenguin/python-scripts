#!/usr/bin/env python

import sys
import subprocess

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

