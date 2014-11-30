#!/usr/bin/env python

from threading import Thread, Event, Lock

class input_buffer(object):
    """The shared input buffer between the main thread and the stdin thread"""
    def __init__(self):
        self.lock = Lock()
        self.buf = ''

    def add(self, data):
        """Add data to the buffer"""
        self.lock.acquire()
        try:
            self.buf += data
        finally:
            self.lock.release()

    def get(self):
        """Get the content of the buffer"""
        self.lock.acquire()
        try:
            data = self.buf
            if data:
                self.buf = ''
                return data
        finally:
            self.lock.release()

