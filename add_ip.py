#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Import system libs
import os
import re
import sys
import time
import optparse
import logging
import subprocess
from datetime import datetime
from logging.handlers import RotatingFileHandler

script = os.path.basename(sys.argv[0])
scriptname = os.path.splitext(script)[0]
DEFAULT_LOG = "/var/log/" + scriptname
LOG = logging.getLogger(scriptname)

# ret parameter declear.
RET_OK           = 0
RET_FAILED       = 1
RET_INVALID_ARGS = 2

####################################################
regexes = [
    "^eth.*",
    "^bond.*",
    "^enp.*",
    "^em.*",
    "^dock.*",
    "^lo.*"
    ]

# Regex const var.
combined = "(" + ")|(".join(regexes) + ")"
# '?' in ipregx for mini match.
ipregx = "inet.*?:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
maskregx = "inet.*:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
argrex = "^(\d{1,3}\.)+(\d{1,3})$"
dgateregx = "^default via (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
ngateregx = "10.0.0.0/8 via (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
# used in checkargs
intprefix = "10."
changeprefix = "11."
rclocal = "/etc/rc.d/rc.local"


def check_args(oldprefix, newprefix):
    if oldprefix == "" or newprefix == "":
        LOG.error("args must not empty string.")
        return False

    olds = re.split('\.', oldprefix)
    news = re.split('\.', newprefix)
    if len(olds) != len(news):
        LOG.error("args must have same seg separated by '.'")
        return False

    if not oldprefix.startswith(intprefix) or \
       not newprefix.startswith(changeprefix):
        LOG.error("args must start with %s -> %s for args: %s %s", \
                intprefix, changeprefix, oldprefix, newprefix)
        return False

    if not re.match(argrex, oldprefix) or \
       not re.match(argrex, newprefix):
        LOG.error("check format for args: %s -> %s", oldprefix, newprefix)
        return False

    return True

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


def parse_argument():
    """ parse the command line argument. """

    usage = "usage: %prog [options] <10.10> <11.10>"
    parser = optparse.OptionParser(usage=usage) 
    parser.add_option('-d', '--debug', dest="debug",
            default=False, action="store_true",
            help="Debug mode for display cmd, not to run.")

    parser.add_option('-s', '--suffix', dest="suffix",
            default="suffix", action="store",
            help="Suffix string for net dev name: like lo:23:suffix.")

    options, args = parser.parse_args()

    if len(args) != 2:
        parser.error("incorrect number of arguments")

    return options, args


def valid_ip(ipstr):
    try:
        parts = ipstr.split('.')
	if len(parts) != 4:
            return False

        for part in parts:
            if int(part) < 0 or int(part) > 256:
                return False
        return True
    except ValueError:
        return False # one of the 'parts' not convertible to integer
    except (AttributeError, TypeError):
        return False # `ip` isn't even a string

def lines_that_equal(filename, line_to_match):
    try:
        fp = open(filename,"r")
        for line in fp:
            if line.strip() == line_to_match.strip():
                return 1
	return 0
    finally:
	fp.close()


# ################# main route ######################
if __name__ == '__main__':
    setup_logging()
    options, args = parse_argument()

    if not check_args(args[0], args[1]):
        sys.exit(RET_FAILED)

    ########### get ifconfig output
    cmd = "ifconfig"
    ret, output, errout = exec_cmd_with_stderr(cmd)

    if ret != 0:
        LOG.error("run cmd %s failed.", cmd)
        sys.exit(RET_FAILED)

    index = 0
    lines = re.split('\n',output)
    found = False
    ipline = ""
    ips = {}
    masks = {} 
    for index in range(0, len(lines)):
        line = lines[index]
        if len(line) == 0:
            continue

	if re.match(combined, line):
            found = True
            #print index, line

        if found:
            index += 1
            ipline = lines[index]
            dev = line.split(' ', 1)[0]
            m = re.search(ipregx, ipline)

            if m:
                devip = m.group(1)
                #print dev, m.group(1)
                if devip != "" and devip.startswith(intprefix):
                    mask = re.search(maskregx, ipline).group(1)
                    ips[dev] =  devip
                    masks[dev] = mask
            #print index, ipline
            found = False

    ########### get ip r output
    cmd = "ip r"
    ret, output, errout = exec_cmd_with_stderr(cmd)

    if ret != 0:
        LOG.error("run cmd %s failed.", cmd)
        sys.exit(RET_FAILED)

    gateway = ""
    lines = re.split('\n',output)
    gateways = {}
    for line in lines:
        m = re.search(dgateregx, line)
        if m:
            dgateway = m.group(1)
            if dgateway.startswith("10."):
                gateways["default"] = dgateway
            continue

        m = re.search(ngateregx, line)
        if m:
            ngateway = m.group(1)
            if ngateway.startswith("10."):
                gateways["newgate"] = ngateway
    
    ####################################################
    ########### start run action for add ip.
    rcfile = open(rclocal,"a")
    startstr = "\n# Start %s ip %s." % (options.suffix, str(datetime.now()))
    if options.debug:
        print startstr,
    else:
        print startstr,
    	rcfile.write(startstr)

    for key in ips:
        ip = ips[key]
        mask = masks[key] 
        tmpprefix = "%s." % (args[0]) 
        if not ip.startswith(tmpprefix):
            LOG.error("please check %s is right for old ip prefix of %s.", args[0], ip)
            sys.exit(RET_FAILED)

        newip = ip.replace(args[0], args[1])
        if not newip.startswith(args[1]):
            LOG.error("please check %s is right for ip prefix of %s.", args[0], ip)
            sys.exit(RET_FAILED)
        elif not valid_ip(newip):
            LOG.error("%s is not a valid ip.", newip)
            sys.exit(RET_FAILED)

        ifcmd = "ifconfig %s:%s %s netmask %s up \n" % (key, options.suffix, newip, mask)
        routecmd = ""
        subgateway = ""
        if key.startswith("lo:"):
            ifcmd = "ifconfig %s:%s %s broadcast %s netmask %s up \n" % (key, options.suffix, newip, newip, mask)
            routecmd = "route add -host %s dev %s:%s \n" % (newip, key, options.suffix)
        else:
            if "default" in gateways.keys():
                subgateway = gateways["default"].replace(args[0], args[1])
            elif "newgate" in gateways.keys():
                subgateway = gateways["newgate"].replace(args[0], args[1])

            if subgateway == "":
                LOG.error("gateway is empty in add ip: %s", ip)
                sys.exit(RET_FAILED)
            routecmd = "ip r a 11.0.0.0/8 via %s \n" % (subgateway)

        if options.debug:
            print ifcmd,
            print routecmd,
        else:
            print "run:", ifcmd,
            print "run:", routecmd,
            
            ret, output, errout = exec_cmd_with_stderr(ifcmd)
            if ret != 0:
                LOG.error("run cmd %s failed: %s.", ifcmd, errout)
            else:
                if lines_that_equal(rclocal, ifcmd) == 0:
	            rcfile.write(ifcmd)

            ret, output, errout = exec_cmd_with_stderr(routecmd)
            if ret != 0:
                LOG.error("run cmd %s failed: %s.", routecmd, errout)
            else:
                if lines_that_equal(rclocal, routecmd) == 0:
                    rcfile.write(routecmd)

    endstr = "# End %s ip.\n" % (options.suffix)
    if options.debug:
        print endstr,
    else:
        print endstr,
        rcfile.write(endstr)

    if rcfile:
        rcfile.close()
