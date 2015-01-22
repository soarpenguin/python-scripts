#!/usr/bin/env python

"""
Real time log files watcher supporting log rotation.
Original Author: Giampaolo Rodola' <g.rodola [AT] gmail [DOT] com>
http://code.activestate.com/recipes/577968-log-watcher-tail-f-log/
License: MIT
Other hacks (ZMQ, JSON, optparse, ...): lusis
"""

import sys
import os
import time
import errno
import stat
import zmq
import socket
import argparse
import simplejson as json


class LogWatcher(object):
    """Looks for changes in all files of a directory.
    This is useful for watching log file changes in real-time.
    It also supports files rotation.
    Example:
    >>> def callback(filename, lines):
    ...     print filename, lines
    ...
    >>> l = LogWatcher("/var/log/", callback)
    >>> l.loop()
    """

    def __init__(self, folder, callback, extensions=["log"], tail_lines=0):
        """Arguments:
        (str) @folder:
            the folder to watch
        (callable) @callback:
            a function which is called every time a new line in a
            file being watched is found;
            this is called with "filename" and "lines" arguments.
        (list) @extensions:
            only watch files with these extensions
        (int) @tail_lines:
            read last N lines from files being watched before starting
        """
        self.files_map = {}
        self.callback = callback
        self.folder = os.path.realpath(folder)
        self.extensions = extensions
        assert os.path.isdir(self.folder), "%s does not exists" \
                                            % self.folder
        assert callable(callback)
        self.update_files()
        # The first time we run the script we move all file markers at EOF.
        # In case of files created afterwards we don't do this.
        for id, file in self.files_map.iteritems():
            file.seek(os.path.getsize(file.name))  # EOF
            if tail_lines:
                lines = self.tail(file.name, tail_lines)
                if lines:
                    self.callback(file.name, lines)

    def __del__(self):
        self.close()

    def loop(self, interval=0.1, async=False):
        """Start the loop.
        If async is True make one loop then return.
        """
        while 1:
            self.update_files()
            for fid, file in list(self.files_map.iteritems()):
                self.readfile(file)
            if async:
                return
            time.sleep(interval)

    def log(self, line):
        """Log when a file is un/watched"""
        print line

    def listdir(self):
        """List directory and filter files by extension.
        You may want to override this to add extra logic or
        globbling support.
        """
        ls = os.listdir(self.folder)
        if self.extensions:
            return [x for x in ls if os.path.splitext(x)[1][1:] \
                                           in self.extensions]
        else:
            return ls

    @staticmethod
    def tail(fname, window):
        """Read last N lines from file fname."""
        try:
            f = open(fname, 'r')
        except IOError, err:
            if err.errno == errno.ENOENT:
                return []
            else:
                raise
        else:
            BUFSIZ = 1024
            f.seek(0, os.SEEK_END)
            fsize = f.tell()
            block = -1
            data = ""
            exit = False
            while not exit:
                step = (block * BUFSIZ)
                if abs(step) >= fsize:
                    f.seek(0)
                    exit = True
                else:
                    f.seek(step, os.SEEK_END)
                data = f.read().strip()
                if data.count('\n') >= window:
                    break
                else:
                    block -= 1
            return data.splitlines()[-window:]

    def update_files(self):
        ls = []
        for name in self.listdir():
            absname = os.path.realpath(os.path.join(self.folder, name))
            try:
                st = os.stat(absname)
            except EnvironmentError, err:
                if err.errno != errno.ENOENT:
                    raise
            else:
                if not stat.S_ISREG(st.st_mode):
                    continue
                fid = self.get_file_id(st)
                ls.append((fid, absname))

        # check existent files
        for fid, file in list(self.files_map.iteritems()):
            try:
                st = os.stat(file.name)
            except EnvironmentError, err:
                if err.errno == errno.ENOENT:
                    self.unwatch(file, fid)
                else:
                    raise
            else:
                if fid != self.get_file_id(st):
                    # same name but different file (rotation); reload it.
                    self.unwatch(file, fid)
                    self.watch(file.name)

        # add new ones
        for fid, fname in ls:
            if fid not in self.files_map:
                self.watch(fname)

    def readfile(self, file):
        lines = file.readlines()
        if lines:
            self.callback(file.name, lines)

    def watch(self, fname):
        try:
            file = open(fname, "r")
            fid = self.get_file_id(os.stat(fname))
        except EnvironmentError, err:
            if err.errno != errno.ENOENT:
                raise
        else:
            self.log("watching logfile %s" % fname)
            self.files_map[fid] = file

    def unwatch(self, file, fid):
        # file no longer exists; if it has been renamed
        # try to read it for the last time in case the
        # log rotator has written something in it.
        lines = self.readfile(file)
        self.log("un-watching logfile %s" % file.name)
        del self.files_map[fid]
        if lines:
            self.callback(file.name, lines)

    @staticmethod
    def get_file_id(st):
        return "%xg%x" % (st.st_dev, st.st_ino)

    def close(self):
        for id, file in self.files_map.iteritems():
            file.close()
        self.files_map.clear()

def jsonify(line, filename):
    me = socket.gethostname()
    source = "file://%s%s" % (me, filename)
    return json.dumps({'@source':source, '@source_host':me, '@message':line,
                        '@source_path':filename})

if __name__ == '__main__':
    epilog_example="""
    Logstash shipper provides an lightweight method for shipping local
    log files to Logstash.
    It does this using zeromq as the transport. This means you'll need
    a zeromq input somewhere down the road to get the events.
    Events are sent in logstash's json_event format.
    Examples 1: Listening on port 5556 (all interfaces)
        cli: logstash-shipper -a tcp://*:5556 -m bind -p /var/log/
        logstash config:
            input { zeromq {
                type => 'shipper-input'
                mode => 'client'
                topology => 'pushpull'
                address => 'tcp://shipperhost:5556'
              } }
            output { stdout { debug => true } }
    Example 2: Connecting to remote port 5556 on indexer
        cli: logstash-shipper -a tcp://indexer:5556 -m connect -p /var/log/
        logstash config:
            input { zeromq {
                type => 'shipper-input'
                mode => 'server'
                topology => 'pushpull'
                address => 'tcp://*:5556'
              }}
            output { stdout { debug => true } }
    """
    parser = argparse.ArgumentParser(description='Logstash logfile shipper',
                                    epilog=epilog_example,
                                    formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-a', '--address', help='0mq address', required=True,
                        dest='address')
    parser.add_argument('-m', '--mode', help='bind or connect mode',
                        default='bind', choices=['bind','connect'])
    parser.add_argument('-p', '--path', help='path to log files', required=True)
    args = parser.parse_args()
    try:
        ctx = zmq.Context()
        pub = ctx.socket(zmq.PUSH)

        if args.mode == 'bind':
            pub.bind(args.address)
        else:
            pub.connect(args.address)

        def callback(filename, lines):
            for line in lines:
                msg = line.rstrip(os.linesep)
                json_msg = jsonify(msg, filename)
                pub.send(json_msg)
        path = args.path
        l = LogWatcher(path, callback)
        l.loop()
    except KeyboardInterrupt:
        print("shutting down. please wait")
        pub.close()
        ctx.term()
        sys.exit(0)
    except Exception, e:
        print("Unhandled Exception: %s" % str(e))
        sys.exit(1)

