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
Pattern => notes
"""

import time
import pattern
import notestream
import window


class Sequencer:
    """ translate patterns to absolute times and pitch values. """

    def __init__(self, clock):
        self.pending = []
        self.running = []
        self.orphaned = []
        self.tempoclock = clock
        self.step = 0

    def add(self, pattern):
        """ locked on the beat for now. """
        stream = notestream.NoteStream(pattern)
        step = (self.tempoclock.beat() + 1) * 64
        self.pending.append((stream, step))
        return stream

    def remove(self, pattern):
        for stream, step in list(self.pending):
            if stream.pattern == pattern:
                self.pending.remove((stream, step))
                return
        for stream in list(self.running):
            if stream.pattern == pattern:
                self.running.remove(stream)
                return
        for stream in list(self.orphaned):
            if stream.pattern == pattern:
                self.orphaned.remove(stream)
                return
        raise KeyError('stream not found')

    def _check(self):
        """ start pending streams. """
        for stream, step in list(self.pending):
            if step == self.step:
                self.pending.remove((stream, step))
                self.running.append(stream)
            elif step < self.step:
                print 'ORPHANED STREAM! (Try shortening the window length)'
                self.pending.remove((stream, step))
                self.orphaned.append(stream)

    def _next(self):
        """ notes for next step. """
        self._check()
        ret = []
        for stream in list(self.running):
            for note in stream.read():
                ret.append((stream, note))
        self.step += 1
        return ret

    def render(self, window):
        """ return notes for a time window. """
        if not hasattr(self, 'starttime'):
            self.starttime = self.tempoclock.localclock.time()
        sofar = self.tempoclock.localclock.time() - self.starttime
        ret = []
        for i in range(window.steps):
            start = window.begin + window.one_step * i
            for stream, note in self._next():
                stop = start + window.one_step * (note.stop - note.start)
                ret.append((stream, start, stop, note.pitch))
        return ret
