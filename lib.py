#!/usr/bin/env python

import string
import re
import types
from sys import stderr

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
            print >>stderr, "ERROR: unknown key", key
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
if __name__ == '__main__':
    var_list = VarList();
    var_list.append("name");
    print >>stderr, STR(var_list);
