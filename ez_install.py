#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Import system libs
import os
import re
import sys
import argparse
import logging
import subprocess

try:
    import simplejson as json
except ImportError:
    import json

# PY3?
is_py3 = sys.version_info >= (3, 3)

script = os.path.basename(sys.argv[0])
scriptname = os.path.splitext(script)[0]
DEFAULT_LOG = "/var/log/" + scriptname
LOG = logging.getLogger(scriptname)

RET_OK           = 0
RET_FAILED       = 1
RET_INVALID_ARGS = 2
INSTALL_CMD      = "/usr/bin/yum"

def error_exit(msg, status=1):
    LOG.error('%s\n' % msg)
    sys.exit(status)


def shutdown():
    print "exit"

USE_SHELL = sys.platform.startswith("win")
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
            if retry_interval_sec > 0: time.sleep(retry_interval_sec)

    return ret, output, errout

def exec_cmd(cmd_list, retry_times=1, retry_interval_sec=0):
    ret = 0
    output = None

    cmd = []
    cmd.extend(cmd_list)

    while retry_times > 0:
        try:
            output = subprocess.check_output(cmd)
            output = output.rstrip()
            break
        except subprocess.CalledProcessError, er:
            ret = er.returncode
            output = None
            retry_times -= 1
            if retry_interval_sec > 0: time.sleep(retry_interval_sec)

    return (ret, output)

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

    parser = argparse.ArgumentParser()

    parser.add_argument('-v', '--version', action = 'version',
                version = '%(prog)s 1.0'
            )

    parser.add_argument('-f', '--file', action = 'store',
                dest = 'configFile', type = str, required = True,
                help = 'Configure file name for operation.'
            )

    #parser.add_argument('name_or_ip', nargs = 1,
    #            help='''host name or ip for query, ip for exact match.''')

    options = parser.parse_args()

    return parser, options

################# main route ######################
if __name__ == '__main__':
    parser, options = parse_argument()

    setup_logging()
    LOG.setLevel(logging.DEBUG)

    if not os.path.exists(options.configFile):
        errorMessage = "%s is not exists." % options.configFile
        error_exit(errorMessage)

    try:
        f = file(options.configFile)
        LOG.info("Load the json file of %s" % options.configFile)
        jstr = json.load(f, encoding="utf-8")

        #print jstr
        print "\n" + "*" * 60
        LOG.info("Now produce the software section.")
        if "software" in jstr.keys():
            software = jstr["software"]
            for s in software:
                LOG.debug("Now install: %s" % s)
                if len(s.strip()) != 0:
                    cmd = INSTALL_CMD + " install -y " + s
                    ret, output, errout = exec_cmd_with_stderr(cmd)
                    if ret != 0:
                        LOG.error("Run %s failed." % errout)
                    else:
                        #print output
                        if re.findall(r'no package', output, re.MULTILINE|re.IGNORECASE):
                            LOG.error("No package match %s", s)
                        elif re.findall(r'already installed', output, re.MULTILINE|re.IGNORECASE):
                            LOG.info("Package of %s has installed.", s)
                        elif re.findall(r'^Installed', output, re.MULTILINE|re.IGNORECASE):
                            LOG.info("Package of %s install successed.", s)
                        else:
                            LOG.error("Software %s has not installed in unknown reason.", s)

        else:
            LOG.info("No software section for produce.")

        print "\n" + "*" * 60
        LOG.info("Now produce the command section.")
        if "command" in jstr.keys():
            command = jstr["command"]
            for cmd in command:
                LOG.debug("Now rum command: %s" % cmd)
                if len(cmd.strip()) != 0:
                    ret, output, errout = exec_cmd_with_stderr(cmd)
                    if ret != 0:
                        LOG.error("Run cmd %s failed." % errout)
                    else:
                        LOG.info("Run cmd successed %s:\n %s" % (cmd, output))
                        #LOG.info("Run cmd successed: %s." % cmd)
        else:
            LOG.info("No command section for produce.")

    except ValueError:
        error_exit("Check the format of json file of %s" % options.configFile)
    except Exception as e:
        print sys.exc_info()
        sys.exit(RET_FAILED)

