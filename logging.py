#!/usr/bin/env python

import sys
import logging
import os
from logging.handlers import RotatingFileHandler

try:
    LOG_FILENAME = os.path.splitext(__file__)[0] + ".log"
    #LOG_FILENAME = sys.argv[0] + ".log"
except:
    LOG_FILENAME = __file__ + ".log"

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

logger = logging.getLogger()
Rthandler = RotatingFileHandler(
        LOG_FILENAME,
        mode='a',
        maxBytes = 10 * 1024 * 1024,
        backupCount=5
    )
#Rthandler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    fmt = '[%(asctime)s] [%(filename)s:%(lineno)d] [%(levelname)-8s] %(message)s',
    datefmt = '%F %H:%M:%S'
)
Rthandler.setFormatter(formatter)
logger.addHandler(Rthandler)
logger.setLevel(logging.DEBUG)

logger.critical("This is a critical message.")
logger.warning('This is warning message')
logger.info('This is warning message')
