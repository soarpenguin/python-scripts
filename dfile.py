#!/usr/bin/env python

import os
import struct
from shutil import move
from hashlib import md5

class Data(object):

    '''base class for data objects (packets,connections, etc..)
            these objects hold data (appendable array, typically of strings)
            and info members (updateable/accessible as members or as dict via info())
            typically one will extend the Data class and replace the data member
            and associated functions (update,iter,str,repr) with a data() function
            and functions to manipulate the data'''

    def __init__(self, *args, **kwargs):
        self.info_keys = []
        # update with list data
        self.data = list(args)
        # update with keyword data
        self.info(**kwargs)

    def info(self, *args, **kwargs):
        '''update/return info stored in this object
                data can be passwd as dict(s) or keyword args'''
        args = list(args) + [kwargs]
        for a in args:
            for k, v in a.iteritems():
                if k not in self.info_keys:
                    self.info_keys.append(k)
                self.__dict__[k] = v
        return dict((k, self.__dict__[k]) for k in self.info_keys)

    def unpack(self, fmt, data, *args):
        '''unpacks data using fmt to keys listed in args'''
        self.info(dict(zip(args, struct.unpack(fmt, data))))

    def pack(self, fmt, *args):
        '''packs info keys in args using fmt'''
        return struct.pack(fmt, *[self.__dict__[k] for k in args])

    def update(self, *args, **kwargs):
        '''updates data (and optionally keyword args)'''
        self.data.extend(args)
        self.info(kwargs)

    def __iter__(self):
        '''returns each data element in order added'''
        for data in self.data:
            yield data

    def __str__(self):
        '''return string built from data'''
        return ''.join(self.data)

    def __repr__(self):
        return ' '.join(['%s=%s' % (k, v) for k, v in self.info().iteritems()])

    def __getitem__(self, k): return self.__dict__[k]

    def __setitem__(self, k, v): self.__dict__[k] = v

class Blob(Data):

    '''a blob containins a contiguous part of the half-stream
    Members:
            starttime,endtime : start and end timestamps of this blob
            direction : direction of this blob's data 'sc' or 'cs'
            data(): this blob's data
            startoffset,endoffset: offset of this blob start/end in bytes from start of stream
    '''

    # max offset before wrap, default is MAXINT32 for TCP sequence numbers
    MAX_OFFSET = 0xffffffff

    def __init__(self, ts, direction, startoffset):
        self.starttime = ts
        self.endtime = ts
        self.direction = direction
        self.segments = {}  # offset:[segments with offset]
        self.startoffset = startoffset
        self.endoffset = startoffset
        self.info_keys = [
            'starttime', 'endtime', 'direction', 'startoffset', 'endoffset']

    def update(self, ts, data, offset=None):
        # if offsets are not being provided, just keep packets in wire order
        if offset == None:
            offset = self.endoffset
        # buffer each segment in a list, keyed by offset (captures retrans,
        # etc)
        self.segments.setdefault(offset, []).append(data)
        if ts > self.endtime:
            self.endtime = ts
        # update the end offset if this packet goes at the end
        if offset >= self.endoffset:
            self.endoffset = (offset + len(data)) & self.MAX_OFFSET

    def __repr__(self):
        return '%s %s (%s) +%s %d' % (self.starttime, self.endtime, self.direction, self.startoffset, len(self.segments))

    def __str__(self):
        '''returns segments of blob as string'''
        return self.data(padding='')

    def data(self, errorHandler=None, padding=None, overlap=True, caller=None, dup=-1):
        '''returns segments of blob reassembled into a string
           if next segment offset is not the expected offset
           errorHandler(blob,expected,offset) will be called
            blob is a reference to the blob
            if expected<offset, data is missing
            if expected>offset, data is overlapping
           else a KeyError will be raised.
            if the exception is passed and data is missing
             if padding != None it will be used to fill the gap
            if segment overlaps existing data
                 new data is kept if overlap=True
                 existing data is kept if overlap=False
            caller: a ref to the calling object, passed to errorhandler
            dup: how to handle duplicate segments:
                0: use first segment seen
                -1 (default): use last segment seen
        '''
        d = ''
        nextoffset = self.startoffset
        for segoffset in sorted(self.segments.iterkeys()):
            if segoffset != nextoffset:
                if errorHandler:  # errorhandler can mangle blob data
                    if not errorHandler(blob=self, expected=nextoffset, offset=segoffset, caller=caller):
                        continue  # errorhandler determines pass or fail here
                elif segoffset > nextoffset:
                    # data missing and padding specified
                    if padding is not None:
                        if len(padding):
                            # add padding to data
                            d += str(padding) * (segoffset - nextoffset)
                    else:
                        # data missing, and no padding
                        raise KeyError(nextoffset)
                elif segoffset < nextoffset and not overlap:
                    continue  # skip if not allowing overlap
            # advance next expected offset
            nextoffset = (
                segoffset + len(self.segments[segoffset][dup])) & self.MAX_OFFSET
            # append or splice data
            d = d[:segoffset - self.startoffset] + \
                self.segments[segoffset][dup] + \
                d[nextoffset - self.startoffset:]
        return d

    def __iter__(self):
        '''return each segment data in offset order
                for TCP this will return segments ordered but not reassembled
                        (gaps and overlaps may exist)
                for UDP this will return datagrams payloads in capture order,
                        (very useful for RTP or other streaming protocol.)
        '''
        for segoffset in sorted(self.segments.iterkeys()):
            yield self.segments[segoffset][-1]


'''
Mode Constants
'''
FILEONDISK = 1  # Object refers to file already written to disk
FILEINMEMORY = 2  # Object contains file contents in data member

'''
dfile -- Dshell file class.

Extends blob for offset based file chunk (segment) reassembly.
Removes time and directionality from segments.

Decoders can instantiate this class and pass it to
output modules or other decoders.

Decoders can choose to pass a file in memory or already
written to disk.

A dfile object can have one of the following modes:
  FILEONDISK
  FILEINMEMORY

'''


class dfile(Blob):

    def __init__(self, mode=FILEINMEMORY, name=None, data=None, **kwargs):

        # Initialize Segments
        # Only really used in memory mode
        self.segments = {}
        self.startoffset = 0
        self.endoffset = 0

        # Initialize consistent info members
        self.mode = mode
        self.name = name
        self.diskpath = None
        self.info_keys = [
            'mode', 'name', 'diskpath', 'startoffset', 'endoffset']

        # update with additional info
        self.info(**kwargs)
        # update data
        if data != None:
            self.update(data)

    def __iter__(self):
        '''
        Undefined
        '''
        pass

    def __str__(self):
        '''
        Returns filename (string)
        '''
        return self.name

    def __repr__(self):
        '''
        Returns filename (string)
        '''
        return self.name

    def md5(self):
        '''
        Returns md5 of file
          Calculate based on reassembly from FILEINMEMORY
          or loads from FILEONDISK
        '''
        if self.mode == FILEINMEMORY:
            return md5(self.data()).hexdigest()
        elif self.mode == FILEONDISK:
            m = md5()
            fh = open(self.diskpath, 'r')
            m.update(fh.read())
            fh.close()
            return m.hexdigest()
        else:
            return None

    def load(self):
        '''
        Load file from disk.  Converts object to mode FILEINMEMORY
        '''
        if not self.mode == FILEONDISK:
            return False
        try:
            fh = open(self.diskpath, 'r')
            self.update(fh.read())
            fh.close()
            self.mode = FILEINMEMORY
        except:
            return False

    def write(self, path='.', name=None, clobber=False, errorHandler=None, padding=None, overlap=True):
        '''
        Write file contents at location relative to path.
        Name on disk will be based on internal name unless one is provided.

        For mode FILEINMEMORY, file will data() will be called for reconstruction.
          After writing to disk, mode will be changed to FILEONDISK.
        If mode is already FILEONDISK, file will be moved to new location.

        '''
        olddiskpath = self.diskpath
        if name == None:
            name = self.name
        self.diskpath = self.__localfilename(name, path, clobber)
        if self.mode == FILEINMEMORY:
            fh = open(self.diskpath, 'w')
            fh.write(self.data())
            fh.close()
            self.segments = {}
            self.startoffset = 0
            self.endoffset = 0
            return self.diskpath
        elif self.mode == FILEONDISK:
            move(olddiskpath, self.diskpath)
            return self.diskpath

    def update(self, data, offset=None):
        if self.mode != FILEINMEMORY:
            return
        # if offsets are not being provided, just keep packets in wire order
        if offset == None:
            offset = self.endoffset
        # don't buffer duplicate packets
        if offset not in self.segments:
            self.segments[offset] = data
        # update the end offset if this packet goes at the end
        if offset >= self.endoffset:
            self.endoffset = offset + len(data)

    #
    # Generate a local (extracted) filename based on the original
    #
    def __localfilename(self, origname, path='.', clobber=False):
        tmp = origname.replace("\\", "_")
        tmp = tmp.replace("/", "_")
        tmp = tmp.replace(":", "_")
        tmp = tmp.replace("?", "_")
        tmp = tmp.lstrip('_')
        localname = ''
        for c in tmp:
            if ord(c) > 32 and ord(c) < 127:
                localname += c
            else:
                localname += "%%%02X" % ord(c)
        # Truncate (from left) to max filename length on filesystem (-3 in case
        # we need to add a suffix)
        localname = localname[os.statvfs(path).f_namemax * -1:]
        # Empty filename not allowed
        if localname == '':
            localname = 'blank'
        localname = os.path.realpath(os.path.join(path, localname))
        if clobber:
            return localname
        # No Clobber mode, check to see if file exists
        suffix = ''
        i = 0
        while os.path.exists(localname + suffix):
            i += 1
            suffix = "_%02d" % i
        return localname + suffix

