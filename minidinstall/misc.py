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

import os, errno, time, string, re

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
