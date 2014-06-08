import argparse
import logging
import sys
import os

script = os.path.basename(sys.argv[0])
scriptname = os.path.splitext(script)[0]

DEFAULT_LOG = "/var/log/" + scriptname
LOG = logging.getLogger(scriptname)

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

    parser.add_argument('-s', action='store',
                        dest='simple_value',
                        help='Store a simple value'
                    )

    parser.add_argument('-c', action='store_const',
                        dest='constant_value',
                        const='value-to-store',
                        help='Store a constant value'
                    )

    parser.add_argument('-t', action = 'store_true',
                default = False,
                dest = 'boolean_switch',
                help = 'Set a switch to true'
            )

    parser.add_argument('-f', action = 'store_false',
                default = False,
                dest = 'boolean_switch',
                help = 'Set a switch to false'
            )

    parser.add_argument('-a', action = 'append',
                dest = 'collection',
                default = [],
                help = 'Set a switch to false'
            )

    parser.add_argument('--version', action = 'version',
                version = '%(prog)s 1.0'
            )

    results = parser.parse_args()

    return results

if __name__ == '__main__':

    results = parse_argument()

    setup_logging()
    LOG.setLevel(logging.DEBUG)
    LOG.debug("Print option value...")

    print results.simple_value
    print results.constant_value
    print results.boolean_switch
    print results.boolean_switch
    print results.collection
    #print results.collection

