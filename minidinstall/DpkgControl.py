# DpkgControl.py
#
# This module implements control file parsing.
#
# DpkgParagraph is a low-level class, that reads/parses a single paragraph
# from a file object.
#
# DpkgControl uses DpkgParagraph in a loop, pulling out the value of a
# defined key(package), and using that as a key in it's internal
# dictionary.
#
# DpkgSourceControl grabs the first paragraph from the file object, stores
# it in object.source, then passes control to DpkgControl.load, to parse
# the rest of the file.
#
# To test this, pass it a filetype char, a filename, then, optionally,
# the key to a paragraph to display, and if a fourth arg is given, only
# show that field.
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

import re, string
from DpkgDatalist import *
from minidinstall.SignedFile import *
from types import ListType

class DpkgParagraph(DpkgOrderedDatalist):
    caseSensitive = 0
    trueFieldCasing = {}

    def setCaseSensitive( self, value ):    self.caseSensitive = value

    def load( self, f ):
        "Paragraph data from a file object."
        key = None
        value = None
        while 1:
            line = f.readline()
            if not line:
                return
            # skip blank lines until we reach a paragraph
            if line == '\n':
                if not self:
                    continue
                else:
                    return
            line = line[ :-1 ]
            if line[ 0 ] != ' ':
                key, value = string.split( line, ":", 1 )
                if value: value = value[ 1: ]
                if not self.caseSensitive:
                    newkey = string.lower( key )
                    if not self.trueFieldCasing.has_key( key ):
                        self.trueFieldCasing[ newkey ] = key
                    key = newkey
            else:
                if isinstance( value, ListType ):
                    value.append( line[ 1: ] )
                else:
                    value = [ value, line[ 1: ] ]
            self[ key ] = value

    def _storeField( self, f, value, lead = " " ):
        if isinstance( value, ListType ):
            value = string.join( map( lambda v, lead = lead: v and ( lead + v ) or v, value ), "\n" )
        else:
            if value: value = lead + value
        f.write( "%s\n" % ( value ) )

    def _store( self, f ):
        "Write our paragraph data to a file object"
        for key in self.keys():
            value = self[ key ]
            if self.trueFieldCasing.has_key( key ):
                key = self.trueFieldCasing[ key ]
            f.write( "%s:" % key )
            self._storeField( f, value )

class DpkgControl(DpkgOrderedDatalist):

    key = "package"
    caseSensitive = 0

    def setkey( self, key ):        self.key = key
    def setCaseSensitive( self, value ):    self.caseSensitive = value

    def _load_one( self, f ):
        p = DpkgParagraph( None )
        p.setCaseSensitive( self.caseSensitive )
        p.load( f )
        return p

    def load( self, f ):
        while 1:
            p = self._load_one( f )
            if not p: break
            self[ p[ self.key ] ] = p

    def _store( self, f ):
        "Write our control data to a file object"

        for key in self.keys():
            self[ key ]._store( f )
            f.write( "\n" )

class DpkgSourceControl( DpkgControl ):
    source = None

    def load( self, f ):
        f = SignedFile(f)
        self.source = self._load_one( f )
        DpkgControl.load( self, f )

    def __repr__( self ):
        return self.source.__repr__() + "\n" + DpkgControl.__repr__( self )

    def _store( self, f ):
        "Write our control data to a file object"
        self.source._store( f )
        f.write( "\n" )
        DpkgControl._store( self, f )

if __name__ == "__main__":
    import sys
    types = { 'p' : DpkgParagraph, 'c' : DpkgControl, 's' : DpkgSourceControl }
    type = sys.argv[ 1 ]
    if not types.has_key( type ):
        print "Unknown type `%s'!" % type
        sys.exit( 1 )
    file = open( sys.argv[ 2 ], "r" )
    data = types[ type ]()
    data.load( file )
    if len( sys.argv ) > 3:
        para = data[ sys.argv[ 3 ] ]
        if len( sys.argv ) > 4:
            para._storeField( sys.stdout, para[ sys.argv[ 4 ] ], "" )
        else:
            para._store( sys.stdout )
    else:
        data._store( sys.stdout )

# vim:ts=4:sw=4:et:
