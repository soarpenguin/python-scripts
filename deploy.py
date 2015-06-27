#!/usr/bin/python

import os
import re
import sys
import yaml
import argparse
import logging
import subprocess
import pexpect
from logging.handlers import RotatingFileHandler

script = os.path.basename(sys.argv[0])
scriptname = os.path.splitext(script)[0]
DEFAULT_LOG = "/var/log/" + scriptname
LOG = logging.getLogger(scriptname)

# ret parameter declear.
RET_OK           = 0
RET_FAILED       = 1
RET_INVALID_ARGS = 2

INDENT = ' ' * 2
def format_help(help_info, choices=None):
    """ format help infomation string. """

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


def parse_argument():
    """ parse the command line argument. """

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', action = 'version',
                version = '%(prog)s 1.0'
            )

    parser.add_argument('--max-bytes', action = 'store', dest = 'max_bytes',
                type = int, default = 64 * 1024 * 1024,
                help = format_help('Maximum bytes per a logfile.'))

    parser.add_argument('--backup-count', action = 'store',
                dest = 'backup_count', type = int, default = 1,
                help = format_help('Maximum number of logfiles to backup.'))

    parser.add_argument('--logfile', action = 'store', dest='logfile',
                type = str, default = DEFAULT_LOG,
                help = format_help('Filename where logs are written to.'))

    parser.add_argument('-f', '--file', action = 'store', required=True,
                dest = 'file', type = str, #nargs = 1,
                help = format_help('File name for module configure: server list and commands(yaml format).')
            )

    parser.add_argument('-s', '--single', action = 'store_true', dest = 'single_mode', default = False,
                help = format_help('Single mode in deploy one host for observation.')
            )

    parser.add_argument('--action', action = 'store', required=True,
                dest = 'action', type = str,
                help = format_help('Action name for script do. (check,update,deploy,rollback)')
            )

    options = parser.parse_args()

    if (not os.path.exists(options.file)):
        print("Error: Pleace check the file of \"%s\" is exists.\n" % options.file)
        parser.print_usage()
        sys.exit(RET_INVALID_ARGS)

    return parser, options


# This class provides the functionality we want. You only need to look at
# this if you want to know how this works. It only needs to be defined
# once, no need to muck around with its internals.
class switch(object):
    def __init__(self, value):
        self.value = value
        self.fall = False
    def __iter__(self):
        """Return the match method once, then stop"""
        yield self.match
        raise StopIteration
    def match(self, *args):
        """Indicate whether or not to enter a case suite"""
        if self.fall or not args:
            return True
        elif self.value in args: # changed for v1.5, see below
            self.fall = True
            return True
        else:
            return False


def load_yaml_configure(filename):
    """Load yaml format configure file for deploy."""
    confdata = None

    try:
        file = open(filename)
        confdata = yaml.load(file)
    except yaml.YAMLError, exc:
        if hasattr(exc, 'problem_mark'):
            mark = exc.problem_mark
            print('[{0}] error position:({1},{2})'.format(filename, mark.line+1, mark.column+1))
    finally:
        file.close()

    return confdata


def expect_and_print(child):
    index = child.expect_exact(['$', '#', '(yes/no)?'])
    if index == 2:
        print child.before, '(yes/no)?'
        child.sendline('yes')
        expect_and_print(child)
    else:
        print child.before, '$',


def do_action(action, confdata, singlemode=False):

    if confdata.has_key(str(action)):
        confdata = confdata.get(action)
    else:
        print('No \'{0}\' section in your configure file!'.format(action))
        sys.exit(RET_FAILED)

#print(confdata)
    if singlemode:
        if len(confdata["servers"]):
            s = confdata["servers"][0]
            do_one_action(s, confdata)
    else:
        for s in confdata["servers"]:
            do_one_action(s, confdata)


def do_one_action(host, confdata):

    if not host or not confdata:
        print("Please check the host and confdata, skip this host action.")
    else:
        print('\n=================================== {0} ===\n'.format(host))

        cmd = 'ssh root@' + host
        child = pexpect.spawn(cmd, timeout=300)
        child.delaybeforesend = 0.1
        child.maxread = 10000

        expect_and_print(child)
        if confdata.has_key("cmds"):
#          exp = 'export PS1="[\u@`hostname`]$"'
#          child.sendline(exp)
           for c in confdata["cmds"]:
#               print(c)
                child.sendline(c)
                expect_and_print(child)

        child.close()

        print('\n=== Over ===\n')


def main():
    args, options = parse_argument()

    setup_logging(options.logfile, options.max_bytes or None,
                  options.backup_count or None)

    filename = os.path.realpath(options.file)
    if filename:
        confdata = load_yaml_configure(filename)

    if confdata is None:
        print("ERROR: Load yaml configure file failed.")
        sys.exit(RET_FAILED)

    action = options.action
    for case in switch(action):
        LOG.info('[{0}] action on [{1}]'.format(action, filename))
        if case('check'):
            print('-------------Now doing in action: {0}'.format(action))
            print yaml.dump(confdata, indent=4, default_flow_style=False)
            break
        if case('update'):
            print('-------------Now doing in action: {0}'.format(action))
            do_action(action, confdata)
            break
        if case('deploy'):
            print('-------------Now doing in action: {0}, Single mode: {1}'.format(action, options.single_mode))
            single_mode = options.single_mode
            do_action(action, confdata, single_mode)
            break
        if case('rollback'):
            print('-------------Now doing in action: {0}'.format(action))
            print('------- Not implement yet for action: {0}'.format(action))
            break
        if case():
            print('-------------Unsupport action, check your action: {0}'.format(action))
            # No need to break here, it'll stop anyway


if __name__ == '__main__':
    main()
