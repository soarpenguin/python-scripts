import urllib
import sys
import time
import socket
import struct
import datetime

def xor(input, key):
    """
    Xor an input string with a given character key.
    """
    output = ''.join([chr(ord(c) ^ key) for c in input])
    return output

# decode_base64 - decodes Base64 text with (optional) custom alphabet
#
def decode_base64(intext, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/', padchar='=', debug=False):

    # Build dictionary from alphabet
    b64DictDec = {}
    i = 0
    for c in alphabet:
        if c in b64DictDec:
            print '%c already exists in alphabet' % (c)
            sys.exit(-1)
        b64DictDec[c] = i
        i += 1

    b64DictDec[padchar] = 0
    alphabet += padchar

    outtext = ''

    # support DOS and Unix line endings
    intext = intext.rstrip('\r\n')

    i = 0
    while i < len(intext) - 3:
        if intext[i] not in alphabet or intext[i + 1] not in alphabet or intext[i + 2] not in alphabet or intext[i + 3] not in alphabet:
            if debug:
                sys.stderr.write(
                    "Non-alphabet character found in chunk: %s\n" % (hexPlusAscii(intext[i:i + 4])))
            if debug:
                sys.stderr.write("Input: %s" % hexPlusAscii(intext))
            raise Exception
        val = b64DictDec[intext[i]] * 262144
        val += b64DictDec[intext[i + 1]] * 4096
        val += b64DictDec[intext[i + 2]] * 64
        val += b64DictDec[intext[i + 3]]
        i += 4
        for factor in [65536, 256, 1]:
            outtext += chr(int(val / factor))
            val = val % factor

    return outtext


# printableUnicode - returns unicode text minus control characters
#
# Author: amm
# Input:  intext (unicode string)
#         onlyText (bool)
#            False = print tab and line-feed chars
#            True = Don't print tab and line-feed chars
# Output: unicode string
#
# Reference: http://en.wikipedia.org/wiki/Unicode_control_characters
#
UNICODE_CONTROL_CHARS = [unichr(x) for x in range(
    0, 9) + [11, 12] + range(14, 0x20) + [0x7f] + range(0x80, 0xA0)]


def printableUnicode(intext, onlyText=False):
    if not type(intext) == unicode:
        # Attempt to cast it
        try:
            intext = unicode(intext)
        except:
            try:
                intext = unicode(intext, 'utf-8')
            except:
                return unicode(printableText(intext, onlyText))
    if onlyText:
        return ''.join([x for x in intext if x not in UNICODE_CONTROL_CHARS + [u'\t', u'\n', u'\r']])
    else:
        return ''.join([x for x in intext if x not in UNICODE_CONTROL_CHARS])

# hexPlusAscii - returns two-column hex/ascii display text for binary input
#
# Author: amm
# Input:  indata (string/binary)
#         width (optional, bytes of hex to display per line)
#         offset (optional, byte offset for display)
# Output: string
#


def hexPlusAscii(data, width=16, offset=0):
    FILTER_hex_display = ''.join(
        [(len(repr(chr(x))) == 3) and chr(x) or '.' for x in range(256)])
    dlen = len(data)
    output = ''
    for i in xrange(0, dlen, width):
        s = data[i:i + width]
        hexa = ' '.join(["%02X" % ord(x) for x in s])
        printable = s.translate(FILTER_hex_display)
        output += "%08X   %-*s   %s\n" % (i +
                                          offset, 16 * 3 + 1, hexa, printable)
    return output

# URLDataToParameterDict - parses URL format string (i.e. the stuff after
#                          the question mark) and returns dictionary
#                          of parameters
#
# Author: amm
# Input:  urldata (string)
# Output: dictionary, indexed by parameter names
# Requires: urllib
#


def URLDataToParameterDict(data):
    if not ' ' in data:
        p, kwp = strtok(data, sep='&')
        return dict((urllib.unquote(k), urllib.unquote(kwp[k]))for k in kwp.keys())

# strtok - string tokenizer a lot like C strtok
# Author: twp
# Input: a string, optionally a param sep and a key/value sep, as_list will force a list even if 0/1 params
# Output: tuple of: None or string or list of params, dictionary indexed by key=value names of k/v params
# Example : a,b,c=d,e=f returns ([a,b],{c:d,e:f})


def strtok(data, sep=',', kvsep='=', as_list=False):
    kwparams = {}
    params = []
    for p in data.split(sep):
        if kvsep in p:
            (k, v) = p.split(kvsep, 1)
            kwparams[k.strip()] = v.strip()
        else:
            params.append(p.strip())
    if not as_list:
        if not len(params):
            params = None
        elif len(params) == 1:
            params = params[0]
    return params, kwparams

# mktime: if python timestamp object convery back to POSIX timestamp
# utctime: return UTC POSIX timestamp
# Author tparker


def mktime(ts):
    if type(ts) == datetime.datetime:
        return time.mktime(ts.timetuple())
    return ts


def utctime():
    return time.mktime(time.gmtime())

# xordecode(key,data)


def xorStringDecode(key=None, data=None):
    ptext = ''
    for pos in range(0, len(data)):
        ptext += chr(ord(data[pos]) ^ ord(key[pos % len(key)]))
    return ptext


def iptoint(ip): return struct.unpack('!L', socket.inet_aton(ip))[0]

# getHeader - Extracts header information from dpkt HTTP request or response
#             objects.

def getHeader(request_or_response, header_name):
    try:
        httpHdr = request_or_response.headers[header_name]
    except:
        return ''
    if type(httpHdr) == str:
        return httpHdr
    elif type(httpHdr) == list:
        # return unique list joined by ','
        return ', '.join(set(httpHdr))
    else:
        return ''
