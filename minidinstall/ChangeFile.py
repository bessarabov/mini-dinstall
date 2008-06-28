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

import os, re, sys, string, stat
import threading, Queue
import logging
from minidinstall import DpkgControl, SignedFile
from minidinstall import misc

class ChangeFileException(Exception):
    def __init__(self, value):
        self._value = value
    def __str__(self):
        return `self._value`
        
class ChangeFile(DpkgControl.DpkgParagraph):
    md5_re = r'^(?P<md5>[0-9a-f]{32})[ \t]+(?P<size>\d+)[ \t]+(?P<section>[-/a-zA-Z0-9]+)[ \t]+(?P<priority>[-a-zA-Z0-9]+)[ \t]+(?P<file>[0-9a-zA-Z][-+:.,=~0-9a-zA-Z_]+)$'
    sha1_re = r'^(?P<sha1>[0-9a-f]{40})[ \t]+(?P<size>\d+)[ \t]+(?P<file>[0-9a-zA-Z][-+:.,=~0-9a-zA-Z_]+)$'
    sha256_re = r'^(?P<sha256>[0-9a-f]{64})[ \t]+(?P<size>\d+)[ \t]+(?P<file>[0-9a-zA-Z][-+:.,=~0-9a-zA-Z_]+)$'

    def __init__(self): 
        DpkgControl.DpkgParagraph.__init__(self)
        self._logger = logging.getLogger("mini-dinstall")
        
    def load_from_file(self, filename):
        f = SignedFile.SignedFile(open(filename))
        self.load(f)
        f.close()

    def getFiles(self):
        return self._get_checksum_from_changes()['md5']

    def _get_checksum_from_changes(self):
        """ extract checksums and size from changes file """
        output = {}
        hashes = { 'md5': ['files', re.compile(self.md5_re)],
                   'sha1': ['checksums-sha1', re.compile(self.sha1_re)],
                   'sha256': ['checksums-sha256', re.compile(self.sha256_re)]
                 }
        hashes_checked = hashes.copy()

        try:
            self['files']
        except KeyError:
            return []

        for hash in hashes:
            try:
                self[hashes[hash][0]]
            except KeyError:
                self._logger.warn("Can't find %s checksums in changes file" % hash)
                hashes_checked.pop(hash)

        for hash in hashes_checked:
            output[hash] = []
            for line in self[hashes[hash][0]]:
                if line == '':
                    continue
                match = hashes[hash][1].match(line)
                if (match is None):
                    raise ChangeFileException("Couldn't parse file entry \"%s\" in Files field of .changes" % (line,))
                output[hash].append([match.group(hash), match.group('size'), match.group('file') ])
        return output
        
    def verify(self, sourcedir):
        """ verify size and hash values from changes file """
        checksum = self._get_checksum_from_changes()
        for hash in checksum.keys():
            for (hashsum, size, filename) in checksum[hash]:
                self._verify_file_integrity(os.path.join(sourcedir, filename), int(size), hash, hashsum)

            
    def _verify_file_integrity(self, filename, expected_size, hash, expected_hashsum):
        """ check uploaded file integrity """
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
        if (misc.get_file_sum(self, hash, filename) != expected_hashsum):
            raise ChangeFileException("%ssum for %s does not match that specified in .dsc" % (hash, filename,))
        self._logger.debug('Verified %ssum %s and size %s for %s' % (hash, expected_hashsum, expected_size, filename))

# vim:ts=4:sw=4:et:
