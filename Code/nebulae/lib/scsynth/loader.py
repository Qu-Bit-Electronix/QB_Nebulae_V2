#   Copyright (C) 2006 by Patrick Stinson                                 
#   patrickkidd@gmail.com                                                   
#                                                                         
#   This program is free software; you can redistribute it and/or modify  
#   it under the terms of the GNU General Public License as published by  
#   the Free Software Foundation; either version 2 of the License, or     
#   (at your option) any later version.                                   
#                                                                         
#   This program is distributed in the hope that it will be useful,       
#   but WITHOUT ANY WARRANTY; without even the implied warranty of        
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         
#   GNU General Public License for more details.                          
#                                                                         
#   You should have received a copy of the GNU General Public License     
#   along with this program; if not, write to the                         
#   Free Software Foundation, Inc.,                                       
#   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.  
#
"""
Manage buffer id's.
"""


class Loader:
    """ manage buffer ids for playing synths. """
    # rename to something buffer related?
    def __init__(self, server):
        self.server = server
        self.server.sendMsg('/notify', 1)

    def load(self, fpath, wait=False, b_query=False):
        """ return a buffer id """
        bid = self.server.bufferpool.get()
##        print bid, '< buffer id'
        if b_query :
            self.server.sendMsg('/b_allocRead', bid, fpath, 0, -1, [ '/b_query', bid ])
        else :
            self.server.sendMsg('/b_allocRead', bid, fpath)
        if wait:
            self.server.receive('/done', '/fail')
        return bid

    def unload(self, bid, wait=False):
        self.server.sendMsg('/b_free', bid)
        if wait:
            self.server.receive('/done', '/fail')
        self.server.bufferpool.recycle(bid)
