def isprintable(instring):
    if isinstance(instring, str):
        #http://stackoverflow.com/a/3637294
        import string
        printset = set(string.printable)
        isprintable = set(instring).issubset(printset)
        return isprintable
    else:
        return True

def count_newlines_from_end(str):
    i = len(str)
    while i > 0:
        if str[i-1] != '\n':
            break
        i -= 1
    return len(str) - i

#: Aliases for the utf-8 codec
_UTF8_ALIASES = frozenset(('utf-8', 'UTF-8', 'utf8', 'UTF8', 'utf_8', 'UTF_8',
    'utf', 'UTF', 'u8', 'U8'))
#: Aliases for the latin-1 codec
_LATIN1_ALIASES = frozenset(('latin-1', 'LATIN-1', 'latin1', 'LATIN1',
    'latin', 'LATIN', 'l1', 'L1', 'cp819', 'CP819', '8859', 'iso8859-1',
    'ISO8859-1', 'iso-8859-1', 'ISO-8859-1'))

def to_unicode(obj, encoding='utf-8', errors='replace', nonstring=None):
    '''Convert an object into a :class:`unicode` string '''

    # Could use isbasestring/isunicode here but we want this code to be as
    # fast as possible
    if isinstance(obj, basestring):
        if isinstance(obj, unicode):
            return obj
        if encoding in _UTF8_ALIASES:
            return unicode(obj, 'utf-8', errors)
        if encoding in _LATIN1_ALIASES:
            return unicode(obj, 'latin-1', errors)
        return obj.decode(encoding, errors)

    if not nonstring:
        nonstring = 'simplerepr'
    if nonstring == 'empty':
        return u''
    elif nonstring == 'passthru':
        return obj
    elif nonstring == 'simplerepr':
        try:
            simple = obj.__unicode__()
        except (AttributeError, UnicodeError):
            simple = None
        if not simple:
            try:
                simple = str(obj)
            except UnicodeError:
                try:
                    simple = obj.__str__()
                except (UnicodeError, AttributeError):
                    simple = u''
        if isinstance(simple, str):
            return unicode(simple, encoding, errors)
        return simple
    elif nonstring in ('repr', 'strict'):
        obj_repr = repr(obj)
        if isinstance(obj_repr, str):
            obj_repr = unicode(obj_repr, encoding, errors)
        if nonstring == 'repr':
            return obj_repr
        raise TypeError('to_unicode was given "%(obj)s" which is neither'
            ' a byte string (str) or a unicode string' %
            {'obj': obj_repr.encode(encoding, 'replace')})

    raise TypeError('nonstring value, %(param)s, is not set to a valid'
        ' action' % {'param': nonstring})
