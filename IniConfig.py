# -*- coding: utf-8 -*-
#
"""Manage the configuration file."""

# Import system libs
import os
import sys
try:
    from configparser import RawConfigParser
    from configparser import NoOptionError
except ImportError:  # Python 2
    from ConfigParser import RawConfigParser
    from ConfigParser import NoOptionError

# PY3?
is_py3 = sys.version_info >= (3, 3)

# Path definitions
work_path = os.path.realpath(os.path.dirname(__file__))
appname_path = os.path.split(sys.argv[0])[0]
sys_prefix = os.path.realpath(os.path.dirname(appname_path))

class IniConfig(object):

    """This class is used to access/read config file, if it exists.

        :param config_file: the config file name
        :type config_file: str or None
    """

    def __init__(self, filename=None):
        self.config_file = filename

        self.parser = RawConfigParser()
        self.load()

    def load(self, encoding='utf-8'):
        """Load a config file from the list of paths, if it exists."""
        config_file = self.config_file
        if os.path.isfile(config_file) and os.path.getsize(config_file) > 0:
            try:
                if is_py3:
                    self.parser.read(config_file, encoding=encoding)
                else:
                    self.parser.read(config_file)
                # print(_("DEBUG: Read configuration file %s") % config_file)
            except UnicodeDecodeError as e:
                print(_("Error: Cannot decode configuration file '{0}': {1}").format(config_file, e))
                sys.exit(1)

    def items(self, section):
        """Return the items list of a section."""
        return self.parser.items(section)

    def has_section(self, section):
        """Return info about the existence of a section."""
        return self.parser.has_section(section)

    def get_option(self, section, option):
        """Get the float value of an option, if it exists."""
        try:
            value = self.parser.getfloat(section, option)
        except NoOptionError:
            return
        else:
            return value

    def get_raw_option(self, section, option):
        """Get the raw value of an option, if it exists."""
        try:
            value = self.parser.get(section, option)
        except NoOptionError:
            return
        else:
            return value

if __name__ == '__main__':

    config_file = "./config.conf"
    if os.path.isfile(config_file):
        config = IniConfig(config_file)

        print config.items("test")
        print config.get_raw_option("test", "name")

