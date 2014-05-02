#!/usr/bin/env python

import re
import sys 
import time
import resource

def main():

    interval = 15
    page_size = resource.getpagesize()

    try:
        sockstat = open("/proc/net/sockstat")
        #netstat = open("/proc/net/netstat")
        #snmp = open("/proc/net/snmp")
    except IOError, e:
        print >>sys.stderr, "open failed: %s" % e 
        return 13  # Ask tcollector to not re-start us.

    regexp = re.compile("sockets: used \d+\n"
                        "TCP: inuse (?P<tcp_inuse>\d+) orphan (?P<orphans>\d+)"
                        " tw (?P<tw_count>\d+) alloc (?P<tcp_sockets>\d+)"
                        " mem (?P<tcp_pages>\d+)\n"
                        "UDP: inuse (?P<udp_inuse>\d+)"
                        # UDP memory accounting was added in v2.6.25-rc1
                        "(?: mem (?P<udp_pages>\d+))?\n"
                        # UDP-Lite (RFC 3828) was added in v2.6.20-rc2
                        "(?:UDPLITE: inuse (?P<udplite_inuse>\d+)\n)?"
                        "RAW: inuse (?P<raw_inuse>\d+)\n"
                        "FRAG: inuse (?P<ip_frag_nqueues>\d+)"
                        " memory (?P<ip_frag_mem>\d+)\n")

    def print_sockstat(metric, value, tags=""):  # Note: tags must start with ' '
        if value is not None:
            print "net.sockstat.%s %d %s%s" % (metric, ts, value, tags)

    while True:
        ts = int(time.time())
        sockstat.seek(0)
        #netstat.seek(0)
        #snmp.seek(0)
        data = sockstat.read()
        #netstats = netstat.read()
        #snmpstats = snmp.read()
        m = re.match(regexp, data)
        if not m:
            print >>sys.stderr, "Cannot parse sockstat: %r" % data
            return 13

        print_sockstat("num_sockets",   m.group("tcp_sockets"),   " type=tcp")
        print_sockstat("num_timewait",  m.group("tw_count"))
        print_sockstat("sockets_inuse", m.group("tcp_inuse"),     " type=tcp")
        print_sockstat("sockets_inuse", m.group("udp_inuse"),     " type=udp")
        print_sockstat("sockets_inuse", m.group("udplite_inuse"), " type=udplite")
        print_sockstat("sockets_inuse", m.group("raw_inuse"),     " type=raw")

        print_sockstat("num_orphans", m.group("orphans"))
        print_sockstat("memory", int(m.group("tcp_pages")) * page_size,
                       " type=tcp")
        if m.group("udp_pages") is not None:
          print_sockstat("memory", int(m.group("udp_pages")) * page_size,
                         " type=udp")
        print_sockstat("memory", m.group("ip_frag_mem"), " type=ipfrag")
        print_sockstat("ipfragqueues", m.group("ip_frag_nqueues"))

        print >>sys.stderr, "------------------------------------------------------"

        sys.stdout.flush()
        time.sleep(interval)

if __name__ == '__main__':
    sys.exit(main())
        
