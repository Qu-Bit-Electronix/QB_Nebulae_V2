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
Supercollider client-side engine.

The supercollider server (scsynth) responds to timestamped events that
load files, play sounds, etc. Because the server has a limited message
buffer (1024), we have to send messages as a stream in real-time. The
challenge is getting the messages in early enough that the server can
process them, while not sending too many as to override the buffer. We
also have to take latency into account, which makes this a much bigger
bundle of fun.

In order to keep the server filled with messages we have to use a
sliding time window to scan ahead and choose which messages to send
from the various sources.

Currently, the only sources that exist in this module are Pattern
objects. A Sequencer object translates patterns into timestamped
messages, which are sent to the server via a Player object, which
handles the gritty gory job of managing notes while they are playing.

CONCEPTS
--------
render for window
  the window never changes, but can

COMPONENTS
==========
 - Sequencer
    - Pattern (Notes)

    - Player
      - Synth(dict)
      - Effect(dict)

PLAY A NOTE
-----------
synth = synths.Synth('MySine')
ctl = scsynth.start()
player = player.Player(ctl)
player.play(synth, time.time() + 1, time.time() + 2)

PLAY A PATTERN
--------------
synth = synths.Synth('MySine')
ctl = scsynth.start()
player = player.Player(ctl)

note = pattern.Note(0, 16, 69)
patt = pattern.Pattern([note])

window = sequencer.Window()
window.update()
for synth, start, stop, pitch in sequencer.render(window):
    player.play(synth, start, stop)
window.close()
"""

from server import start, connect, startServer
from pattern import Note, Pattern
from pattern import read as read_pattern, write as write_pattern
from pool import Pool, AutoPool, IntPool
from player import Player, Synth, Effect
from loader import Loader
from tempoclock import TempoClock
from sequencer import Sequencer
from window import Window
from notestream import NoteStream
