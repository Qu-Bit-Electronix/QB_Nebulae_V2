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
A file-like pattern interface, good for looping.
"""

import pattern


class NoteStream:
    """ serial, loopable file interface to a note pattern. """

    def __init__(self, pattern):
        self.pattern = pattern
        self.looping = True
        self.cursor = 0
        
    def loop(self, on):
        self.looping = bool(on)

    def notes_for_step(self, step):
        """ notes for the current step
        
        THIS IS O(n)!!!
        """
        loop_cursor = step % (self.pattern.beats * 64)
        return [note for note in list(self.pattern)
                if note.start == loop_cursor]

    def to_looptime(self, notes):
        """ correct pattern times to loop times. """
        ret = []
        loops = self.cursor / (self.pattern.beats * 64)
        offset = loops * self.pattern.beats * 64
        for note in notes:
            loopnote = pattern.Note(note.start + offset,
                                    note.stop + offset,
                                    note.pitch)
            ret.append(loopnote)
        return ret
        
    def read(self):
        """ read one step """
        if self.looping is False and self.cursor >= self.pattern.beats * 64:
            return []
        notes = self.notes_for_step(self.cursor)
        ret = self.to_looptime(notes)
        self.cursor += 1
        return ret
