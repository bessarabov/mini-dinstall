# misc -*- mode: python; coding: utf-8 -*-

# misc tools for mini-dinstall

# Copyright © 2004 Thomas Viehmann <tv@beamnet.de>

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

import os, errno, time, string, re, popen2

def dup2(fd,fd2):
  # dup2 with EBUSY retries (cf. dup2(2) and Debian bug #265513)
  success = 0
  tries = 0
  while (not success):
    try:
      os.dup2(fd,fd2)
      success = 1
    except OSError, e:
      if (e.errno != errno.EBUSY) or (tries >= 3):
	raise
      # wait 0-2 seconds befor next try
      time.sleep(tries)
      tries += 1

def format_changes(L):
    """ remove changelog header and all lines with only a dot """

    dotmatch = re.compile('^\.$')
    L1 = []

    for x in L[3:]:
        L1.append(dotmatch.sub('', x))

    return "\n".join(L1)

def get_file_sum(self, type, filename):
    """ generate hash sums for file """
    ret = _get_external_file_sum(self, type, filename)
    if not ret:
        ret = _get_internal_file_sum(type, filename)
    return ret

def _get_internal_file_sum(type, filename):
    """ generate hash sums for file with python modules """
    if type == 'md5':
        import md5
        sum = md5.new()
    elif type == 'sha1':
        import sha
        sum = sha.new()
    elif type == 'sha256':
        from Crypto.Hash import SHA256
        sum = SHA256.new()
    f = open(filename)
    buf = f.read(8192)
    while buf != '':
        sum.update(buf)
        buf = f.read(8192)
    return sum.hexdigest()

def _get_external_file_sum(self, type, filename):
    """ generate hash sums for file with external programs """
    ret = None
    if os.access('/usr/bin/%ssum' % (type,), os.X_OK):
        cmd = '/usr/bin/%ssum %s' % (type, filename,)
        self._logger.debug("Running: %s" % (cmd,))
        child = popen2.Popen3(cmd, 1)
        child.tochild.close()
        erroutput = child.childerr.read()
        child.childerr.close()
        if erroutput != '':
            child.fromchild.close()
            raise DinstallException("%ssum returned error output \"%s\"" % (type, erroutput,))
        (sum, filename) = string.split(child.fromchild.read(), None, 1)
        child.fromchild.close()
        try:
            status = child.wait()
        except OSError, (errnum, err):
            if errnum == 10:
                logger.warn("Ignoring missing child proccess")
                status = 0
        if not (status is None or (os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0)):
            if os.WIFEXITED(status):
                msg = "%ssum exited with error code %d" % (type, os.WEXITSTATUS(status),)
            elif os.WIFSTOPPED(status):
                msg = "%ssum stopped unexpectedly with signal %d" % (type, os.WSTOPSIG(status),)
            elif os.WIFSIGNALED(status):
                msg = "%ssum died with signal %d" % (type, os.WTERMSIG(status),)
            raise DinstallException(msg)
        ret = sum.strip()
    return ret
