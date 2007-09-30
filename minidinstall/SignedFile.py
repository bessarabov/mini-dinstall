# SignedFile -*- mode: python; coding: utf-8 -*-

# SignedFile offers a subset of file object operations, and is
# designed to transparently handle files with PGP signatures.

# Copyright © 2002 Colin Walters <walters@gnu.org>
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import re,string

class SignedFile:
    _stream = None
    _eof = 0
    _signed = 0
    _signature = None
    _signatureversion = None
    _initline = None
    def __init__(self, stream):
        self._stream = stream
        line = stream.readline()
        if (line == "-----BEGIN PGP SIGNED MESSAGE-----\n"):
            self._signed = 1
            while (1):
                line = stream.readline()
                if (len(line) == 0 or line == '\n'):
                    break
        else:
            self._initline = line

    def readline(self):
        if self._eof:
            return ''
        if self._initline:
            line = self._initline
            self._initline = None
        else:
            line = self._stream.readline()
        if not self._signed:
            return line
        elif line == "-----BEGIN PGP SIGNATURE-----\n":
            self._eof = 1
            self._signature = []
            self._signatureversion = self._stream.readline()
            self._stream.readline()  # skip blank line
            while 1:
                line = self._stream.readline()
                if len(line) == 0 or line == "-----END PGP SIGNATURE-----\n":
                    break
                self._signature.append(line)
            self._signature = string.join
            return ''
        return line
            
    def readlines(self):
        ret = []
        while 1:
            line = self.readline()
            if (line != ''):
                ret.append(line)
            else:
                break
        return ret

    def close(self):
        self._stream.close()

    def getSigned(self):
        return self._signed

    def getSignature(self):
        return self._signature

    def getSignatureVersion(self):
        return self._signatureversion
            
if __name__=="__main__":
    import sys
    if len(sys.argv) == 0:
        print "Need one file as an argument"
        sys.exit(1)
    filename = sys.argv[1]
    f=SignedFile(open(filename))
    if f.getSigned():
        print "**** SIGNED ****"
    else:
        print "**** NOT SIGNED ****"
    lines=f.readlines()
    print lines
    if not f.getSigned():
        assert(len(lines) == len(actuallines))
    else:
        print "Signature: %s" % (f.getSignature())

# vim:ts=4:sw=4:et:
