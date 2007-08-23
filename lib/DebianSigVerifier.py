# DebianSigVerifier -*- mode: python; coding: utf-8 -*-

# A class for verifying signed files, using Debian keys

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

import os, re, sys, string, stat, logging
from minidinstall.GPGSigVerifier import GPGSigVerifier

class DebianSigVerifier(GPGSigVerifier):
    _dpkg_ring = '/etc/dpkg/local-keyring.gpg'
    def __init__(self, keyrings=None, extra_keyrings=None):
        if keyrings is None:
            keyrings = ['/usr/share/keyrings/debian-keyring.gpg', '/usr/share/keyrings/debian-keyring.pgp']
        if os.access(self._dpkg_ring, os.R_OK):
            keyrings.append(self._dpkg_ring)
        if not extra_keyrings is None:
            keyrings += extra_keyrings
        GPGSigVerifier.__init__(self, keyrings)

# vim:ts=4:sw=4:et:
