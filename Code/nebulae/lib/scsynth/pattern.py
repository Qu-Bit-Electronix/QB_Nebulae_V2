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
music baby!

note pitch is measured in half-step increments starting at C-2, and rising to G-8

"""

import container


class Note:
    """ a note in music units. """
    
    start = None
    stop = None
    pitch = 0

    def __init__(self, start, stop, pitch):
        self.start = start
        self.stop = stop
        self.pitch = pitch

    def calc_abs(self, spb):
        sps = spb / 64.0
        return self.start * sps, self.stop * sps

    def __str__(self):
        return '<%s (start %i, stop %i, pitch %i)>' % (self.__class__.__name__,
                                                       self.start,
                                                       self.stop,
                                                       self.pitch)

    def __eq__(self, note):
        if note.start != self.start:
            return False
        if note.stop != self.stop:
            return False
        if note.pitch != self.pitch:
            return False
        return True

def note_cmp(a, b):
    if a.start >= b.start:
        return 1
    elif a.start == b.start:
        return 0
    else:
        return -1


class Pattern(container.ListProxy):
    """ an ordered list of notes. 
    - shared data between engine and views.
    """

    name = None
    synth = None
    beats = None

    def __init__(self, beats=4):
        container.ListProxy.__init__(self)
        self.beats = beats

    def __str__(self):
        s = "<%s (%i notes)>" % (self.__class__.__name__, len(self))
        for note in self:
            s += '\n    '+str(note)
        return s
    __repr__ = __str__

    def add(self, note):
        i = 0
        prev = None
        if not note in self:
            self.append(note)
            self.sort(note_cmp)

    def notes_for(self, start, stop):
        """ return notes for a time window. """
        return [n for n in self if n.start >= start and n.stop < stop]

    def copy(self):
        newone = self.__class__()
        for note in self:
            newone.add(Note(note.start, note.stop, note.pitch))
        newone.name = self.name
        newone.beats = self.beats
        newone.synth = self.synth
        return newone


def toelem(pattern, elem):
    from elementtree.ElementTree import SubElement
    patt = SubElement(elem, 'pattern')
    patt.attrib['name'] = str(pattern.name)
    patt.attrib['beats'] = str(pattern.beats)
    for note in pattern:
        sub = SubElement(patt, 'note')
        sub.attrib['start'] = str(note.start)
        sub.attrib['stop'] = str(note.stop)
        sub.attrib['pitch'] = str(note.pitch)

def write(pattern, fpath):
    import os
    from elementtree.ElementTree import Element, ElementTree
    root = Element('xml')
    toelem(pattern, root)
    ElementTree(root).write(fpath)
    os.system('tidy -xml -iqm \"%s\"' % fpath)


def read(fpath):
    from elementtree.ElementTree import parse
    root = parse(fpath).getroot()
    for patt in root:
        pattern = Pattern()
        pattern.name = patt.get('name')
        pattern.beats = int(patt.get('beats'))
        for note in patt:
            start = int(note.get('start'))
            stop = int(note.get('stop'))
            pitch = int(note.get('pitch'))
            pattern.add(Note(start, stop, pitch))
        if pattern.name == 'None':
            pattern.name = None
        return pattern
