#!/usr/bin/env python
# -*- coding: utf-8 -*-

import multiprocessing
#import procname
import time

""" Usage of multiprocessing, attention for use SIGTERM kill Receiver go deadlock. """

class Receiver(multiprocessing.Process):
    ''' Reads from queue with 3 secs timeout '''

    def __init__(self, queue):
        multiprocessing.Process.__init__(self)
        self.queue = queue

    def run(self):
        #procname.setprocname('Receiver')
        while True:
            try:
                msg = self.queue.get(timeout=3)
                print '<<< `{}`, queue rlock: {}'.format(
                    msg, self.queue._rlock)
            except multiprocessing.queues.Empty:
                print '<<< EMPTY, Queue rlock: {}'.format(
                    self.queue._rlock)
                pass


class Worker(multiprocessing.Process):
    ''' Puts into queue with 1 sec sleep '''

    def __init__(self, queue):
        multiprocessing.Process.__init__(self)
        self.queue = queue

    def run(self):
        #procname.setprocname('Worker')
        while True:
            time.sleep(1)
            print 'Worker: putting msg, Queue size: ~{}'.format(
                self.queue.qsize())
            self.queue.put('msg from Worker')


if __name__ == '__main__':
    queue = multiprocessing.Queue()

    worker = Worker(queue)
    worker.start()

    receiver = Receiver(queue)
    receiver.start()

    while True:
        time.sleep(1)
        if not worker.is_alive():
            print 'Restarting worker'
            worker = Worker(queue)
            worker.start()
        if not receiver.is_alive():
            print 'Restarting receiver'
            receiver = Receiver(queue)
            receiver.start()

