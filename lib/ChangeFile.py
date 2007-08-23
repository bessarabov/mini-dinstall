# ChangeFile

# A class which represents a Debian change file.

# Copyright 2002 Colin Walters <walters@gnu.org>

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

import os, re, sys, string, stat, popen2
import threading, Queue
import logging
from minidinstall import DpkgControl, SignedFile

class ChangeFileException(Exception):
    def __init__(self, value):
        self._value = value
    def __str__(self):
        return `self._value`
        
class ChangeFile(DpkgControl.DpkgParagraph):
    def __init__(self): 
        DpkgControl.DpkgParagraph.__init__(self)
        self._logger = logging.getLogger("mini-dinstall")
        
    def load_from_file(self, filename):
        f = SignedFile.SignedFile(open(filename))
        self.load(f)
        f.close()

    def getFiles(self):
        out = []
        try:
            files = self['files']
        except KeyError:
            return []
        lineregexp = re.compile("^([0-9a-f]{32})[ \t]+(\d+)[ \t]+([-/a-zA-Z0-9]+)[ \t]+([-a-zA-Z0-9]+)[ \t]+([0-9a-zA-Z][-+:.,=~0-9a-zA-Z_]+)$")
        for line in files:
            if line == '':
                continue
            match = lineregexp.match(line)
            if (match is None):
                raise ChangeFileException("Couldn't parse file entry \"%s\" in Files field of .changes" % (line,))
            out.append((match.group(1), match.group(2), match.group(3), match.group(4), match.group(5)))
        return out
        
    def verify(self, sourcedir):
        for (md5sum, size, section, prioriy, filename) in self.getFiles():
            self._verify_file_integrity(os.path.join(sourcedir, filename), int(size), md5sum)
            
    def _verify_file_integrity(self, filename, expected_size, expected_md5sum):
        self._logger.debug('Checking integrity of %s' % (filename,))
        try:
            statbuf = os.stat(filename)
            if not stat.S_ISREG(statbuf[stat.ST_MODE]):
                raise ChangeFileException("%s is not a regular file" % (filename,))
            size = statbuf[stat.ST_SIZE]
        except OSError, e:
            raise ChangeFileException("Can't stat %s: %s" % (filename,e.strerror))
        if size != expected_size:
            raise ChangeFileException("File size for %s does not match that specified in .dsc" % (filename,))
        if (self._get_file_md5sum(filename) != expected_md5sum):
            raise ChangeFileException("md5sum for %s does not match that specified in .dsc" % (filename,))
        self._logger.debug('Verified md5sum %s and size %s for %s' % (expected_md5sum, expected_size, filename))

    def _get_file_md5sum(self, filename):
        if os.access('/usr/bin/md5sum', os.X_OK):
            cmd = '/usr/bin/md5sum %s' % (filename,)
            self._logger.debug("Running: %s" % (cmd,))
            child = popen2.Popen3(cmd, 1)
            child.tochild.close()
            erroutput = child.childerr.read()
            child.childerr.close()
            if erroutput != '':
                child.fromchild.close()
                raise ChangeFileException("md5sum returned error output \"%s\"" % (erroutput,))
            (md5sum, filename) = string.split(child.fromchild.read(), None, 1)
            child.fromchild.close()
            status = child.wait()
            if not (status is None or (os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0)):
                if os.WIFEXITED(status):
                    msg = "md5sum exited with error code %d" % (os.WEXITSTATUS(status),)
                elif os.WIFSTOPPED(status):
                    msg = "md5sum stopped unexpectedly with signal %d" % (os.WSTOPSIG(status),)
                elif os.WIFSIGNALED(status):
                    msg = "md5sum died with signal %d" % (os.WTERMSIG(status),)
                raise ChangeFileException(msg)
            return md5sum.strip()
        import md5
        f = open(filename)
        md5sum = md5.new()
        buf = f.read(8192)
        while buf != '':
            md5sum.update(buf)
            buf = f.read(8192)
        return md5sum.hexdigest()

# vim:ts=4:sw=4:et:
