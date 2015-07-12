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

def prepare_writeable_dir(tree, mode=0777):
    ''' make sure a directory exists and is writeable '''

    # modify the mode to ensure the owner at least
    # has read/write access to this directory
    mode |= 0700

    # make sure the tree path is always expanded
    # and normalized and free of symlinks
    tree = unfrackpath(tree)

    if not os.path.exists(tree):
        try:
            os.makedirs(tree, mode)
        except (IOError, OSError), e:
            print("Could not make dir %s: %s" % (tree, e))
            sys.exit(1)
    if not os.access(tree, os.W_OK):
        print("Cannot write to path %s" % tree)
        sys.exit(1)
    return tree


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

