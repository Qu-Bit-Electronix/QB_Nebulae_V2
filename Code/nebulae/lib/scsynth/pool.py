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
Manage synth ids and other recyleable stuff.

Re-use before re-cycle!
"""


import time


class Pool:
    def __init__(self):
        self.stale = []
        
    def get(self):
        if self.stale:
            return self.stale.pop()
        else:
            return self.new()
        
    def recycle(self, o):
        self.stale.append(o)

    def new(self):
        pass


class AutoPool(Pool):
    """ automatically reclaim objects after they expire. """
    def __init__(self):
        Pool.__init__(self)
        self.inuse = []
        
    def get(self, exp=None):
        o = Pool.get(self)
        self.inuse.append((exp, o))
        return o
    
    def check(self):
        now = time.time()
        for exp, o in list(self.inuse):
            if exp and exp < now:
                self.inuse.remove((exp, o))
                self.stale.append(o)


class IntPool(AutoPool):
    def __init__(self, start):
        AutoPool.__init__(self)
        self.last_int = start
        
    def new(self):
        self.last_int += 1
        return self.last_int
