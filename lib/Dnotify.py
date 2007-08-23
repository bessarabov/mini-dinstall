# Dnotify -*- mode: python; coding: utf-8 -*-

# A simple FAM-like beast in Python

# Copyright © 2002 Colin Walters <walters@gnu.org>

# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import os, re, sys, string, stat, threading, Queue, time
import logging
from minidinstall import misc

class DnotifyException(Exception):
    def __init__(self, value):
        self._value = value
    def __str__(self):
        return `self._value`

class DirectoryNotifierFactory:
    def create(self, dirs, use_dnotify=1, poll_time=30, logger=None, cancel_event=None):
        if use_dnotify and os.access('/usr/bin/dnotify', os.X_OK):
            if logger:
                logger.debug("Using dnotify directory notifier")
            return DnotifyDirectoryNotifier(dirs, logger)
        else:
            if logger:
                logger.debug("Using mtime-polling directory notifier")
            return MtimeDirectoryNotifier(dirs, poll_time, logger, cancel_event=cancel_event)

class DnotifyNullLoggingFilter(logging.Filter):
    def filter(self, record):
        return 0

class DirectoryNotifier:
    def __init__(self, dirs, logger, cancel_event=None):
        self._cwd = os.getcwd()
        self._dirs = dirs
        if cancel_event is None:
            self._cancel_event = threading.Event()
        else:
            self._cancel_event = cancel_event
        if logger is None:
            self._logger = logging.getLogger("Dnotify")
            self._logger.addFilter(DnotifyNullLoggingFilter())
        else:
            self._logger = logger

    def cancelled(self):
        return self._cancel_event.isSet()

class DirectoryNotifierAsyncWrapper(threading.Thread):
    def __init__(self, dnotify, queue, logger=None, name=None):
        if not name is None:
            threading.Thread.__init__(self, name=name)
        else:
            threading.Thread.__init__(self)
        self._eventqueue = queue
        self._dnotify = dnotify
        if logger is None:
            self._logger = logging.getLogger("Dnotify")
            self._logger.addFilter(DnotifyNullLoggingFilter())
        else:
            self._logger = logger

    def cancel(self):
        self._cancel_event.set()

    def run(self):
        self._logger.info('Created new thread (%s) for async directory notification' % (self.getName()))
        while not self._dnotify.cancelled():
            dir = self._dnotify.poll()
            self._eventqueue.put(dir)
        self._logger.info('Caught cancel event; async dnotify thread exiting')

class MtimeDirectoryNotifier(DirectoryNotifier):
    def __init__(self, dirs, poll_time, logger, cancel_event=None):
        DirectoryNotifier.__init__(self, dirs, logger, cancel_event=cancel_event)
        self._changed = []
        self._dirmap = {}
        self._polltime = poll_time
        for dir in dirs:
            self._dirmap[dir] = os.stat(os.path.join(self._cwd, dir))[stat.ST_MTIME]
    
    def poll(self, timeout=None):
        timeout_time = None
        if timeout:
            timeout_time = time.time() + timeout
        while self._changed == []:
            if timeout_time and time.time() > timeout_time:
                return None
            self._logger.debug('Polling...')
            for dir in self._dirmap.keys():
                oldtime = self._dirmap[dir]
                mtime = os.stat(os.path.join(self._cwd, dir))[stat.ST_MTIME]
                if oldtime < mtime:
                    self._logger.debug('Directory "%s" has changed' % (dir,))
                    self._changed.append(dir)
                self._dirmap[dir] = mtime
            if self._changed == []:
                for x in range(self._polltime):
                    if self._cancel_event.isSet():
                        return None
                    time.sleep(1)
        ret = self._changed[0]
        self._changed = self._changed[1:]
        return ret

class DnotifyDirectoryNotifier(DirectoryNotifier):
    def __init__(self, dirs, logger):
        DirectoryNotifier.__init__(self, dirs, logger)
        self._queue = Queue.Queue()
        dnotify = DnotifyThread(self._queue, self._dirs, self._logger)
        dnotify.start()
        
    def poll(self, timeout=None):
        # delete duplicates
        i = self._queue.qsize()
        self._logger.debug('Queue size: %d', (i,))
        set = {}
        while i > 0:
            dir = self._queue_get(timeout)
            if dir is None:
                # We shouldn't have to do this; no one else is reading
                # from the queue.  But we do it just to be safe.
                for key in set.keys():
                    self._queue.put(key)
                return None
            set[dir] = 1
            i -= 1
        for key in set.keys():
            self._queue.put(key)
        i = self._queue.qsize()
        self._logger.debug('Queue size (after duplicate filter): %d', (i,))
        return self._queue_get(timeout)

    def _queue_get(self, timeout):
        if timeout is None:
            return self._queue.get()
        timeout_time = time.time() + timeout
        while 1:
            try:
                self._queue.get(0)
            except Queue.Empty:
                if time.time() > timeout_time:
                    return None
                else:
                    time.sleep(15)

class DnotifyThread(threading.Thread):
    def __init__(self, queue, dirs, logger):
        threading.Thread.__init__(self)
        self._queue = queue
        self._dirs = dirs
        self._logger = logger
        
    def run(self):
        self._logger.debug('Starting dnotify reading thread')
        (infd, outfd) = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(infd)
            misc.dup2(outfd, 1)
            args = ['dnotify', '-m', '-c', '-d', '-a', '-r'] + list(self._dirs) + ['-e', 'printf', '"{}\\0"']
            os.execv('/usr/bin/dnotify', args)
            os.exit(1)

        os.close(outfd)
        stdout = os.fdopen(infd)
        c = 'x'
        while c != '':
            curline = ''
            c = stdout.read(1)
            while c != '' and c != '\0':
                curline += c
                c = stdout.read(1)
            if c == '':
                break
            self._logger.debug('Directory "%s" changed' % (curline,))
            self._queue.put(curline)
        (pid, status) = os.waitpid(pid, 0)
        if status is None:
            ecode = 0
        else:
            ecode = os.WEXITSTATUS(status)
        raise DnotifyException("dnotify exited with code %s" % (ecode,))

# vim:ts=4:sw=4:et:
