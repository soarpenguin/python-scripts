#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Import system libs
import os
import re
import sys
import time
import argparse
import logging
import subprocess
from logging.handlers import RotatingFileHandler

# PY3?
is_py3 = sys.version_info >= (3, 3)

script = os.path.basename(sys.argv[0])
scriptname = os.path.splitext(script)[0]
DEFAULT_LOG = "/var/log/" + scriptname
LOG = logging.getLogger(scriptname)

# array of file ext for exclude.
EXCLUDE_EXT = (
    "~", ".bak", ".ini", ".pyc", "pyo",
    "tags", ".out"
)

# ret parameter declear.
RET_OK           = 0
RET_FAILED       = 1
RET_INVALID_ARGS = 2

USE_SHELL = sys.platform.startswith("win")


def error_exit(msg, status=RET_FAILED):
    """ error message display and exit."""
    LOG.error('%s\n' % msg)
    sys.exit(status)


def exec_cmd_with_stderr(command,
                         retry_times = 1,
                         retry_interval_sec = 0,
                         universal_newlines = True,
                         useshell = True,
                         env = os.environ):
    ret = 0
    output = None
    errout = None

    while retry_times > 0:
        try:
            p = subprocess.Popen(command,
                              stdout = subprocess.PIPE,
                              stderr = subprocess.PIPE,
                              shell = useshell,
                              universal_newlines = universal_newlines,
                              env = env)

            output = p.stdout.read()
            p.wait()
            errout = p.stderr.read()
            p.stdout.close()
            p.stderr.close()
            ret = p.returncode
            break
        except subprocess.CalledProcessError, er:
            ret = er.returncode
            retry_times -= 1
            if retry_interval_sec > 0:
                time.sleep(retry_interval_sec)

    return ret, output, errout


def setup_logging(logfile=DEFAULT_LOG, max_bytes=None, backup_count=None):
    """Sets up logging and associated handlers."""

    LOG.setLevel(logging.INFO)
    if backup_count is not None and max_bytes is not None:
        assert backup_count > 0
        assert max_bytes > 0
        ch = RotatingFileHandler(logfile, 'a', max_bytes, backup_count)
    else:  # Setup stream handler.
        ch = logging.StreamHandler(sys.stdout)

    ch.setFormatter(logging.Formatter('%(asctime)s %(name)s[%(process)d] '
                                      '%(levelname)s: %(message)s'))
    LOG.addHandler(ch)


def deal_with_file(filename, exts=''):
    """ deal with the file. """

    if filename is None or not os.path.exists(filename):
        errorMessage = "file of %s is not exists." % filename
        LOG.error(errorMessage)
        sys.exit(RET_FAILED)

    # match system sed cmd parameter diff.
    if re.match("Darwin", os.uname()[0], re.I):
        cmd = 'sed -i \'\' \'s/[ ]*$//g\''
    else:
        cmd = 'sed -i \'s/[ \t]*$//g\''

    exts = str(exts).strip()
    extsarray = exts.split(',')

    if extsarray:
        if any(str(filename).endswith(ext) for ext in extsarray):
            cmd = cmd + " " + filename
            print(cmd)
            ret, output, errout = exec_cmd_with_stderr(cmd)
            if ret != 0:
                LOG.error("Run cmd %s failed." % errout)
            else:
                LOG.info("Run cmd successed %s." % cmd)
    else:
        # Skip files that end with certain extensions or characters
        if any(str(filename).endswith(ext) for ext in EXCLUDE_EXT):
            LOG.info("skip the file of %s" % filename)
        elif str(filename).startswith('.') and \
             not str(filename).startswith('./'):
            LOG.info("skip the file of %s" % filename)
        else:
            cmd = cmd + " " + filename
            ret, output, errout = exec_cmd_with_stderr(cmd)
            if ret != 0:
                LOG.error("Run cmd %s failed." % errout)
            else:
                LOG.info("Run cmd successed %s." % cmd)


def deal_with_dir(dirpath, exts=''):
    """ recurse deal with the dir, skip the dir start with '.' """

    if dirpath is None or not os.path.exists(dirpath):
        errorMessage = "dir of %s is not exists." % dirpath
        LOG.error(errorMessage)
        sys.exit(RET_FAILED)

    dirpath = str(dirpath).strip()
    if str(dirpath).startswith('.') and not dirpath.startswith('./'):
        LOG.info("skip the dir of %s" % dirpath)
    else:
        for name in os.listdir(dirpath):
            if not str(name).strip().startswith("."):
                f = os.path.join(dirpath, name)

                if os.path.isdir(f) and os.access(f, os.W_OK) and \
                   not os.path.islink(f):
                    # directory, recurse into it
                    deal_with_dir(f, exts)

                elif os.path.isfile(f) and os.access(f, os.W_OK):
                    # file, deal with the file
                    deal_with_file(f, exts)
                else:
                    LOG.error("deal with the file %s failed" % f)
            else:
                LOG.info("skip the file of %s" % name)


def format_help(help_info, choices=None):
    """ format help infomation string. """

    INDENT = ' ' * 2
    if isinstance(help_info, list):
        help_str_list = help_info[:]
    else:
        help_str_list = [help_info]

    if choices:
        help_str_list.extend([
            '%s%s - %s' % (INDENT, k, v) for k, v in choices.items()
        ])

    help_str_list.append(INDENT + '(DEFAULT: %(default)s)')

    return os.linesep.join(help_str_list)


def parse_argument():
    """ parse the command line argument. """

    epilog_example = """
    rm_end_space provides cmd line tool for remove spaces/tab etc character in
    the end of line. Useful for batch format source code and text file.

    Please see the readme for complete examples.
    """

    parser = argparse.ArgumentParser(description='Cmd line tool for rm spaces in the end of line.',
            epilog = epilog_example, formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-v', '--version', action = 'version',
                version = '%(prog)s 1.0')

    parser.add_argument('--max-bytes', action = 'store', dest = 'max_bytes',
                type = int, default = 64 * 1024 * 1024,
                help = format_help('Maximum bytes per a logfile.'))

    parser.add_argument('--backup-count', action = 'store',
                dest = 'backup_count', type = int, default = 0,
                help = format_help('Maximum number of logfiles to backup.'))

    parser.add_argument('--logfile', action = 'store', dest='logfile',
                type = str, default = DEFAULT_LOG,
                help = format_help('Filename where logs are written to.'))

    parser.add_argument('-e', '--exts', action = 'store',
                dest = 'exts', type = str, default = '',
                help = format_help('Specific file exts for operation, muti exti separated by comma.'))

    parser.add_argument('-d', '--dir', action = 'store',
                dest = 'dir', type = str,
                help = format_help('Dir to recursive remove spaces at the end of the line.'))

    parser.add_argument('-f', '--file', action = 'store',
                dest = 'file', type = str,
                help = format_help('File name for remove spaces at the end of the line.'))

    options = parser.parse_args()

    if (options.file is None and options.dir is None) \
       or (options.file and options.dir):
        print("Error: parameter -d or -f just for one.\n")
        parser.print_usage()
        sys.exit(RET_FAILED)

    return parser, options

# ################# main route ######################
if __name__ == '__main__':

    parser, options = parse_argument()

    setup_logging(options.logfile, options.max_bytes or None,
                  options.backup_count or None)

    LOG.setLevel(logging.DEBUG)

    if options.dir is not None and not os.path.exists(options.dir):
        errorMessage = "dir of %s is not exists." % options.dir
        error_exit(errorMessage)
    elif options.file is not None and not os.path.exists(options.file):
        errorMessage = "file of %s is not exists." % options.file
        error_exit(errorMessage)

    try:
        if options.file is not None:
            filename = os.path.basename(options.file)
            if not str(filename).startswith('.'):
                options.file = os.path.abspath(options.file)
                deal_with_file(options.file, options.exts)
            else:
                LOG.info("skip the file of %s." % filename)
        elif options.dir is not None:
            options.dir = os.path.abspath(options.dir)
            deal_with_dir(options.dir, options.exts)
        else:
            LOG.error("Error: parameter -d or -f must have one.")
    except Exception as e:
        print(sys.exc_info())
        sys.exit(RET_FAILED)
