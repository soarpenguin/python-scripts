#!/usr/bin/env python

import logging
from logging.handlers import RotatingFileHandler

#logging.basicConfig(
#        level=logging.DEBUG,
#        format='[%(asctime)s] [%(filename)s:%(lineno)d] [%(levelname)s] %(message)s',
#        #datefmt='%a, %d %b %Y %H:%M:%S',
#        datefmt='%F %H:%M:%S',
#        filename='myapp.log',
#        filemode='w+'
#)
#
#logging.debug('This is debug message')
#logging.info('This is info message')
#logging.warning('This is warning message')


Rthandler = RotatingFileHandler(
        'myapp.log', 
        mode='a',
        maxBytes = 10*1024*1024,
        backupCount=5
    )
#Rthandler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    fmt = '[%(asctime)s] [%(filename)s:%(lineno)d] [%(levelname)-8s] %(message)s',
    datefmt = '%F %H:%M:%S'
)
Rthandler.setFormatter(formatter)
logging.getLogger('').addHandler(Rthandler) 

logging.critical("This is a critical message.")
logging.warning('This is warning message')
