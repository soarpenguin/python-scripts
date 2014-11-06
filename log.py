"""A simple log mechanism styled after PEP 282."""

# The class here is styled after PEP 282 so that it could later be
# replaced with a standard Python logging implementation.

DEBUG = 1
INFO = 2
WARN = 3
ERROR = 4
FATAL = 5

import sys
import os
import logging
import logging.handlers

class Log:

    def __init__(self, threshold=WARN):
        self.threshold = threshold

    def _log(self, level, msg, args):
        if level not in (DEBUG, INFO, WARN, ERROR, FATAL):
            raise ValueError('%s wrong log level' % str(level))

        if level >= self.threshold:
            if args:
                msg = msg % args
            if level in (WARN, ERROR, FATAL):
                stream = sys.stderr
            else:
                stream = sys.stdout
            if stream.errors == 'strict':
                # emulate backslashreplace error handler
                encoding = stream.encoding
                msg = msg.encode(encoding, "backslashreplace").decode(encoding)
            stream.write('%s\n' % msg)
            stream.flush()

    def log(self, level, msg, *args):
        self._log(level, msg, args)

    def debug(self, msg, *args):
        self._log(DEBUG, msg, args)

    def info(self, msg, *args):
        self._log(INFO, msg, args)

    def warn(self, msg, *args):
        self._log(WARN, msg, args)

    def error(self, msg, *args):
        self._log(ERROR, msg, args)

    def fatal(self, msg, *args):
        self._log(FATAL, msg, args)

_global_log = Log()
log = _global_log.log
debug = _global_log.debug
info = _global_log.info
warn = _global_log.warn
error = _global_log.error
fatal = _global_log.fatal

def set_threshold(level):
    # return the old threshold for use from tests
    old = _global_log.threshold
    _global_log.threshold = level
    return old

def set_verbosity(v):
    if v <= 0:
        set_threshold(WARN)
    elif v == 1:
        set_threshold(INFO)
    elif v >= 2:
        set_threshold(DEBUG)


def init_log(log_path, level = logging.INFO, when = 'D', backup = 7,
		format = '[%(levelname)8s]: %(asctime)s: %(filename)s:%(lineno)d * %(thread)d %(message)s',
		datefmt = '%Y-%m-%d %H:%M:%S', filemode = 'a+', debug_console = False):

	"""
	Args:
	    log_path: log file path prefix
	    level: DEBUG < INFO < WARNING < ERROR < CRITICAL
	            the default value is logging.INFO
	    when: how to split the log file by time interval
	      'S': Seconds
		  'M': Minutes
		  'H': Hours
		  'D': Days
		  'W': Week day
		 default value: 'D'
        format: formate of log
	    backup: how many backup file to keep
	            default value is 7
	"""

	formatter = logging.Formatter(format, datefmt)
	logger = logging.getLogger()
	logger.setLevel(level)

	dir = os.path.dirname(log_path)
	if not os.path.isdir(dir):
		os.makedirs(dir)

	handler = logging.handlers.TimedRotatingFileHandler(log_path + '.log', \
			when = when, backupCount = backup)
	handler.setLevel(level)
	handler.setFormatter(formatter)
	logger.addHandler(handler)

	handler = logging.handlers.TimedRotatingFileHandler(log_path + '.log.wf', \
			when = when, backupCount = backup)
	handler.setLevel(logging.WARNING)
	handler.setFormatter(formatter)
	logger.addHandler(handler)

	if debug_console == True:
		_setup_console()

def _setup_console():
	console = logging.StreamHandler()
	console.setLevel(logging.DEBUG)
	formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
	console.setFormatter(formatter)
	logging.getLogger().addHandler(console)

