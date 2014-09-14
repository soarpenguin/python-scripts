#!/usr/bin/env python

import glob
import os
import sys

from setuptools import setup, find_packages

def get_requires():
    requires = ['psutil>=2.0.0']
    if sys.platform.startswith('win'):
        requires += ['colorconsole']
    if sys.version_info < (2, 7):
        requires += ['argparse']

    return requires

def get_data_files():
    data_files = [
        ('share/doc/' + __appname__, ['AUTHORS', 'COPYING', 'NEWS', 'README.md']),
        ('share/man/man1', ['man/' + __appname__ + ".1"])
    ]

    if hasattr(sys, 'real_prefix') or 'bsd' in sys.platform:
        conf_path = os.path.join(sys.prefix, 'etc', __appname__)
    elif not hasattr(sys, 'real_prefix') and 'linux' in sys.platform:
        conf_path = os.path.join('/etc', __appname__)
    elif 'darwin' in sys.platform:
        conf_path = os.path.join('/usr/local', 'etc', __appname__)
    elif 'win32' in sys.platform:
        conf_path = os.path.join(os.environ.get('APPDATA'), __appname__)
    data_files.append((conf_path, ['conf/' + __appname__ + '.conf']))

    return data_files

__appname__ = "python-scripts"

setup(

    ### Metadata
    name = __appname__,
    version = '0.1.0',
    description = 'Useful python scripts.',
    long_description = open('README.md').read(),
    url = 'https://github.com/soarpenguin/python-scripts',
    #download_url = 'https://github.com/soarpenguin/python-scripts/'
    license = 'GPL',
    author = 'soarpenguin',
    author_email = 'soarpenguin@gmail.com',

    maintainer = 'soarpenguin',
    maintainer_email = 'soarpenguin@gmail.com',

    ### Dependencies
    install_requires = get_requires(),
    #packages = ["logging"],
    packages = find_packages(),
    include_package_data = True,
    data_files = get_data_files(),
    #test_suite="unitest.py",
    #entry_points={"console_scripts": ["glances=glances:main"]},

    ### Contents
    #packages = find_packages(exclude=['tests*']),
)

