# SafeWriteFile.py
#
# This file is a writable file object.  It writes to a specified newname,
# and when closed, renames the file to the realname.  If the object is
# deleted, without being closed, this rename isn't done.  If abort() is
# called, it also disables the rename.
#
# Copyright 2001 Adam Heath <doogie@debian.org>
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

from types import StringType
from shutil import copy2
from string import find
from os import rename

class ObjectNotAllowed(Exception):
    pass


class InvalidMode(Exception):
    pass


class SafeWriteFile:
    def __init__(self, newname, realname, mode="w", bufsize=-1):

        if type(newname)!=StringType:
            raise ObjectNotAllowed(newname)
        if type(realname)!=StringType:
            raise ObjectNotAllowed(realname)

        if find(mode, "r")>=0:
            raise InvalidMode(mode)
        if find(mode, "a")>=0 or find(mode, "+") >= 0:
            copy2(realname, newname)
        self.fobj=open(newname, mode, bufsize)
        self.newname=newname
        self.realname=realname
        self.__abort=0

    def close(self):
        self.fobj.close()
        if not (self.closed and self.__abort):
            rename(self.newname, self.realname)

    def abort(self):
        self.__abort=1

    def __del__(self):
        self.abort()
        del self.fobj

    def __getattr__(self, attr):
        try:
            return self.__dict__[attr]
        except:
            return eval("self.fobj." + attr)


if __name__ == "__main__":
    import time
    f=SafeWriteFile("sf.new", "sf.data")
    f.write("test\n")
    f.flush()
    time.sleep(1)
    f.close()

# vim:ts=4:sw=4:et:
