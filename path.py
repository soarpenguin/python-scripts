from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import stat
from errno import EEXIST

__all__ = ['is_executable', 'unfrackpath']

def is_executable(path):
    '''is the given path executable?'''
    return (stat.S_IXUSR & os.stat(path)[stat.ST_MODE] or stat.S_IXGRP & os.stat(path)[stat.ST_MODE] or stat.S_IXOTH & os.stat(path)[stat.ST_MODE])

def unfrackpath(path):
    '''
    returns a path that is free of symlinks, environment
    variables, relative path traversals and symbols (~)
    example:
    '$HOME/../../var/mail' becomes '/var/spool/mail'
    '''
    return os.path.normpath(os.path.realpath(os.path.expandvars(os.path.expanduser(path))))

def makedirs_safe(path, mode=None):
    '''Safe way to create dirs in muliprocess/thread environments'''
    if not os.path.exists(path):
        try:
            if mode:
                os.makedirs(path, mode)
            else:
                os.makedirs(path)
        except OSError, e:
            if e.errno != EEXIST:
                raise

