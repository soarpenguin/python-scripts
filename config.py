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

# Global information
appname = 'config'

# PY3?
is_py3 = sys.version_info >= (3, 3)

# Operating system flag
# Note: Somes libs depends of OS
is_bsd = sys.platform.find('bsd') != -1
is_linux = sys.platform.startswith('linux')
is_mac = sys.platform.startswith('darwin')
is_windows = sys.platform.startswith('win')

# Path definitions
work_path = os.path.realpath(os.path.dirname(__file__))
appname_path = os.path.split(sys.argv[0])[0]
sys_prefix = os.path.realpath(os.path.dirname(appname_path))

class Config(object):

    """This class is used to access/read config file, if it exists.

    :param location: the custom path to search for config file
    :type location: str or None
    """

    def __init__(self, location=None):
        self.location = location
        self.config_filename = appname + '.conf'

        self.parser = RawConfigParser()
        self.load()

    def load(self, encoding='utf-8'):
        """Load a config file from the list of paths, if it exists."""
        for config_file in self.get_config_paths():
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
                break

    def get_config_paths(self):
        r"""Get a list of config file paths. """
        paths = []
        conf_path = os.path.realpath(os.path.join(work_path, '..', '..', 'conf'))

        if self.location is not None:
            #paths.append(self.location)
            paths.append(os.path.join(self.location, self.config_filename))

        if os.path.exists(conf_path):
            paths.append(os.path.join(conf_path, self.config_filename))

        if is_linux or is_bsd:
            paths.append(os.path.join(
                os.environ.get('XDG_CONFIG_HOME') or os.path.expanduser('~/.config'),
                appname, self.config_filename))
            if hasattr(sys, 'real_prefix') or is_bsd:
                paths.append(os.path.join(sys.prefix, 'etc', appname, self.config_filename))
            else:
                paths.append(os.path.join('/etc', appname, self.config_filename))
        elif is_mac:
            paths.append(os.path.join(
                os.path.expanduser('~/Library/Application Support/'),
                appname, self.config_filename))
            paths.append(os.path.join(
                sys_prefix, 'etc', appname, self.config_filename))
        elif is_windows:
            paths.append(os.path.join(
                os.environ.get('APPDATA'), appname, self.config_filename))

        return paths

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
        config = Config("./")

        print config.items("test")
        print config.get_raw_option("test", "name")
