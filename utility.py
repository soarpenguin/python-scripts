#!/usr/bin/env python
#-*-coding:utf-8-*-

import sys
import subprocess
import ConfigParser

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

if __name__ == '__main__':
    configvalue = getConfig("./config.ini", "mysql", "port")
    print configvalue
#assert expression1, expression2
#if __debug__:
#    if not expression1: raise AssertionError(expression2)
