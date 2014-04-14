from __future__ import print_function

import os
import os.path
import sys

def main():
  if len(sys.argv) != 4:
    print("usage: tasks.py <folder> <exts> <tags>")
    sys.exit(1)

  folder = sys.argv[1]
  exts = sys.argv[2].split(',')
  tags = sys.argv[3].split(',')

  os.path.walk(folder, scan_folder, (exts, tags))

def scan_folder((exts, tags), dirname, names):
  for name in names:
    (root, ext) = os.path.splitext(name)
    if ext in exts:
      scan_file(os.path.join(dirname, name), tags)

def scan_file(filename, tags):
  f = open(filename, 'r')
  for line_num, line in enumerate(f):
    for tag in tags:
      if tag in line:
        print("[%s] %s (%d)  %s" % (tag, filename, line_num, line[:-1].strip()))

if __name__ == "__main__":
  main()
