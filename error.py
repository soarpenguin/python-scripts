#!/usr/bin/env python
# -*- coding: utf-8 -*-

class FlattenerError(Exception):
    """
    An error occurred while flattening an object.

    @ivar _roots: A list of the objects on the flattener's stack at the time
        the unflattenable object was encountered.  The first element is least
        deeply nested object and the last element is the most deeply nested.
    """
    def __init__(self, exception, roots, traceback):
        self._exception = exception
        self._roots = roots
        self._traceback = traceback
        Exception.__init__(self, exception, roots, traceback)


    def _formatRoot(self, obj):
        """
        Convert an object from C{self._roots} to a string suitable for
        inclusion in a render-traceback (like a normal Python traceback, but
        can include "frame" source locations which are not in Python source
        files).

        @param obj: Any object which can be a render step I{root}.
            Typically, L{Tag}s, strings, and other simple Python types.

        @return: A string representation of C{obj}.
        @rtype: L{str}
        """
        # There's a circular dependency between this class and 'Tag', although
        # only for an isinstance() check.
        if isinstance(obj, (str, unicode)):
            # It's somewhat unlikely that there will ever be a str in the roots
            # list.  However, something like a MemoryError during a str.replace
            # call (eg, replacing " with &quot;) could possibly cause this.
            # Likewise, UTF-8 encoding a unicode string to a byte string might
            # fail like this.
            if len(obj) > 40:
                if isinstance(obj, str):
                    prefix = 1
                else:
                    prefix = 2
                return repr(obj[:20])[:-1] + '<...>' + repr(obj[-20:])[prefix:]
            else:
                return repr(obj)
        else:
            return repr(obj)


    def __repr__(self):
        """
        Present a string representation which includes a template traceback, so
        we can tell where this error occurred in the template, as well as in
        Python.
        """
        # Avoid importing things unnecessarily until we actually need them;
        # since this is an 'error' module we should be extra paranoid about
        # that.
        from traceback import format_list
        if self._roots:
            roots = '  ' + '\n  '.join([
                    self._formatRoot(r) for r in self._roots]) + '\n'
        else:
            roots = ''
        if self._traceback:
            traceback = '\n'.join([
                    line
                    for entry in format_list(self._traceback)
                    for line in entry.splitlines()]) + '\n'
        else:
            traceback = ''
        return (
            'Exception while flattening:\n' +
            roots + traceback +
            self._exception.__class__.__name__ + ': ' +
            str(self._exception) + '\n')


    def __str__(self):
        return repr(self)

