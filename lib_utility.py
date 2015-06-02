"""Exceptions used throughout the package.

Submodules of distutils2 may raise exceptions defined in this module as
well as standard exceptions; in particular, SystemExit is usually raised
for errors that are obviously the end-user's fault (e.g. bad
command-line arguments).
"""


class PackagingError(Exception):
    """The root of all Packaging evil."""

class PackagingFileError(PackagingError):
    """Any problems in the filesystem: expected file not found, etc.
    Typically this is for problems that we detect before IOError or
    OSError could be raised."""

class PackagingPlatformError(PackagingError):
    """We don't know how to do something on the current platform (but
    we do know how to do it on some platform) -- eg. trying to compile
    C files on a platform not supported by a CCompiler subclass."""


###########################################################################
import os

""" utility  """
_PLATFORM = None

def newer(source, target):
    """Tell if the target is newer than the source.

    Returns true if 'source' exists and is more recently modified than
    'target', or if 'source' exists and 'target' doesn't.

    Returns false if both exist and 'target' is the same age or younger
    than 'source'. Raise PackagingFileError if 'source' does not exist.

    Note that this test is not very accurate: files created in the same second
    will have the same "age".
    """
    if not os.path.exists(source):
        raise PackagingFileError("file '%s' does not exist" %
                                 os.path.abspath(source))
    if not os.path.exists(target):
        return True

    return os.stat(source).st_mtime > os.stat(target).st_mtime


_environ_checked = False

def check_environ():
    """Ensure that 'os.environ' has all the environment variables needed.

    We guarantee that users can use in config files, command-line options,
    etc.  Currently this includes:
      HOME - user's home directory (Unix only)
      PLAT - description of the current platform, including hardware
             and OS (see 'get_platform()')
    """
    global _environ_checked
    if _environ_checked:
        return

    if os.name == 'posix' and 'HOME' not in os.environ:
        import pwd
        os.environ['HOME'] = pwd.getpwuid(os.getuid())[5]

    #if 'PLAT' not in os.environ:
    #    os.environ['PLAT'] = get_platform()

    _environ_checked = True

def assert_raises(exception_cls, callable, *args, **kwargs):
    try:
        callable(*args, **kwargs)
    except exception_cls as e:
        return e
    except Exception as e:
        assert False, 'assert_raises %s but raised: %s' % (exception_cls, e)
    assert False, 'assert_raises %s but nothing raise' % (exception_cls)

def assert_fail(err_response, callable, *args, **kwargs):
    try:
        callable(*args, **kwargs)
    except Exception as e:
        assert re.search(err_response, str(e)), \
               'assert "%s" but got "%s"' % (err_response, e)
        return

    assert False, 'assert_fail %s but nothing raise' % (err_response)

if __name__ == "__main__":
    print newer("utility.py", "util.py")

    check_environ()
    print _environ_checked
