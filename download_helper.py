#!/usr/bin/env python
#-*-coding:utf-8-*-
#

import subprocess
import sys
import os
import tempfile
import shutil
import contextlib
import zipfile
import platform
import re
from distutils import log
from urlparse import urlparse

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

def _python_cmd(*args):
    """
    Return True if the command succeeded.
    """
    args = (sys.executable,) + args
    return subprocess.call(args) == 0

class ContextualZipFile(zipfile.ZipFile):
    """
    Supplement ZipFile class to support context manager for Python 2.6
    """

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def __new__(cls, *args, **kwargs):
        """
        Construct a ZipFile or ContextualZipFile as appropriate
        """
        if hasattr(zipfile.ZipFile, '__exit__'):
            return zipfile.ZipFile(*args, **kwargs)
        return super(ContextualZipFile, cls).__new__(cls)

@contextlib.contextmanager
def archive_context(filename):
    # extracting the archive
    tmpdir = tempfile.mkdtemp()
    log.warn('Extracting in %s', tmpdir)
    old_wd = os.getcwd()
    try:
        os.chdir(tmpdir)
        with ContextualZipFile(filename) as archive:
            archive.extractall()

        # going in the directory
        subdir = os.path.join(tmpdir, os.listdir(tmpdir)[0])
        os.chdir(subdir)
        log.warn('Now working in %s', subdir)
        yield

    finally:
        os.chdir(old_wd)
        shutil.rmtree(tmpdir)

def _clean_check(cmd, target):
    """
    Run the command to download target. If the command fails, clean up before
    re-raising the error.
    """
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError:
        if os.access(target, os.F_OK):
            os.unlink(target)
        raise

def download_file_powershell(url, target):
    """
    Download the file at url to target using Powershell (which will validate
    trust). Raise an exception if the command cannot complete.
    """
    target = os.path.abspath(target)
    ps_cmd = (
        "[System.Net.WebRequest]::DefaultWebProxy.Credentials = "
        "[System.Net.CredentialCache]::DefaultCredentials; "
        "(new-object System.Net.WebClient).DownloadFile(%(url)r, %(target)r)"
        % vars()
    )
    cmd = [
        'powershell',
        '-Command',
        ps_cmd,
    ]
    _clean_check(cmd, target)

def has_powershell():
    if platform.system() != 'Windows':
        return False
    cmd = ['powershell', '-Command', 'echo test']
    with open(os.path.devnull, 'wb') as devnull:
        try:
            subprocess.check_call(cmd, stdout=devnull, stderr=devnull)
        except Exception:
            return False
    return True

download_file_powershell.viable = has_powershell

def download_file_curl(url, target):
    cmd = ['curl', url, '--silent', '--output', target]
    _clean_check(cmd, target)

def has_curl():
    cmd = ['curl', '--version']
    with open(os.path.devnull, 'wb') as devnull:
        try:
            subprocess.check_call(cmd, stdout=devnull, stderr=devnull)
        except Exception:
            return False
    return True

download_file_curl.viable = has_curl

def download_file_wget(url, target):
    cmd = ['wget', url, '--quiet', '--output-document', target]
    _clean_check(cmd, target)

def has_wget():
    cmd = ['wget', '--version']
    with open(os.path.devnull, 'wb') as devnull:
        try:
            subprocess.check_call(cmd, stdout=devnull, stderr=devnull)
        except Exception:
            return False
    return True

download_file_wget.viable = has_wget

def download_file_insecure(url, target):
    """
    Use Python to download the file, even though it cannot authenticate the
    connection.
    """
    src = urlopen(url)
    try:
        # Read all the data in one block.
        data = src.read()
    finally:
        src.close()

    # Write all the data in one block to avoid creating a partial file.
    with open(target, "wb") as dst:
        dst.write(data)

download_file_insecure.viable = lambda: True

def get_best_downloader():
    downloaders = (
        download_file_powershell,
        download_file_curl,
        download_file_wget,
        download_file_insecure,
    )
    viable_downloaders = (dl for dl in downloaders if dl.viable())
    return next(viable_downloaders, None)


def main():
    url = "http://code.jquery.com/jquery-2.1.1.js"
    parsed = urlparse(url)
    saveto = re.sub('[\\\/]', '', parsed.path)
    saveto = os.path.join(os.curdir, saveto)
    downloader = get_best_downloader()
    downloader(url, saveto)
    pass

if __name__ == '__main__':
    sys.exit(main())
