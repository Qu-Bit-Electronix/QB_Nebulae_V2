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
"""


class Window:
    """ A sliding time window. """

    # writable
    lead = .01
    length = .01
    # read-only
    one_step = None
    steps = 0
    begin = None
    end = None
    
    def __init__(self, tempoclock):
        self.tempoclock = tempoclock
        self.begin = self.end = self.tempoclock.localclock.time()

    def update(self):
        """ calculate the new end of the time window? """
        abs_end = self.tempoclock.localclock.time() + self.lead + self.length
        self.one_step = self.tempoclock.spb() / 64
        self.steps = int((abs_end - self.end) / self.one_step)
        self.end += self.steps * self.one_step

    def close(self):
        self.begin = self.end
