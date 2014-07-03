#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

class Timer(object):

    """The timer class. A simple chronometer."""

    def __init__(self, duration):
        self.duration = duration
        self.start()

    def start(self):
        self.target = time.time() + self.duration

    def reset(self):
        self.start()

    def set(self, duration):
        self.duration = duration

    def finished(self):
        return time.time() > self.target

if __name__ == '__main__':
    timer = Timer(100)

    timer.start()

    while not timer.finished():
        time.sleep(1)
        print "time"
