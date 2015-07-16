#!/usr/bin/env python

import os
import subprocess
import sys

dir = sys.argv[1]

if not dir or not os.path.exists(dir):
    print("Please check the path: %s" % dir)
    sys.exit(1)

list = os.listdir(dir)

for item in list:
    subprocess.call('rpm -qf %s/%s' % (dir, item), shell = True)
