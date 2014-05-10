#!/usr/bin/env python

import socket as socket_mod

s = socket_mod.socket(socket_mod.AF_PACKET, socket_mod.SOCK_RAW, socket_mod.IPPROTO_IP)
s.bind(('eth1', 0x0800))

## the public network interface
#HOST = socket.gethostbyname(socket.gethostname())

# create a raw socket and bind it to the public interface
#s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.IPPROTO_IP)
#s.bind((HOST, 0))

# Include IP headers
#s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

# receive all packages
#s.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

while True:
	# receive a package
	print s.recvfrom(65565)

# disabled promiscuous mode
#s.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
