#!/usr/bin/env python
#
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
tempo scheduling.
"""

import time


class TempoClock:
    """ scalable, and always forward-sequential """
    
    bpm = None

    def __init__(self, bpm, localclock=time):
        self.bpm = float(bpm)
        self.localclock = localclock
        self.recent = self.localclock.time()
        self.beats = 0
        
    def update(self):
        now = self.localclock.time()
        elapsed_beats = (now - self.recent) / self.spb()
        self.beats = int(self.beats) + elapsed_beats
        self.recent += int(elapsed_beats) * self.spb()

    def spb(self):
        """ seconds per beat """
        return 60.0 / self.bpm

    def beat(self):
        """ current beat, 0-indexed """
        self.update()
        return int(self.beats)

    def step(self):
        """ current step, 0-indexed """
        self.update()
        return int(self.beats * 64.0)

    def time(self, beat):
        self.update()
        delta = (beat - self.beats) * self.spb()
        return self.recent + delta

    def set_tempo(self, bpm):
        self.update()
        # old state
        now = self.localclock.time()
        elapsed_beats = int((now - self.recent) / self.spb())
        self.recent += elapsed_beats * self.spb()
        frac = (now - self.recent) / self.spb()
        # new state
        self.bpm = float(bpm)
        self.recent = now - (frac * self.spb())


def run_clock():
    clock = TempoClock(140)
    time.sleep(1)
    clock.set_tempo(150)
    last = 0.0
    while True:
        time.sleep(.01)
        next = clock.next_beat_abs()
        if next != last:
            last = next
            print next


def metronome():
    import os
    import sys
    import scosc

    PATH = os.path.join(os.path.expanduser('~'),
                        '.pksampler', 'synthdefs')
    SYNTHS = ('JASStereoSamplePlayer.scsyndef',
              'JASSine.scsyndef')

    BUFID = 0
    SAMPLEID = 1000
    FPATH = '/Users/patrick/.pksampler/click.wav'
    CLICK = ['/s_new', 'JASStereoSamplePlayer', -1, 1, 0, 'bufnum', BUFID, 'loopIt', 0]

    controller = scosc.Controller(('127.0.0.1', 57110), verbose=False)
    controller.sendMsg('/notify', 1)
    controller.sendMsg('/dumpOSC', 1)
    controller.sendMsg('/status', 1)
    for synth in SYNTHS:
        controller.sendMsg('/d_load', os.path.join(PATH, synth))
        controller.receive('/done', '/fail')
    controller.sendMsg('/b_allocRead', BUFID, FPATH)
    controller.receive('/done', '/fail')

    clock = TempoClock(140.0)
    now = time.time() + .5
    for i in range(10):
        next = now + clock.spb() * i
        clock.set_tempo(clock.bpm * 0.95)
        controller.sendBundleAbs(next, [CLICK])


if __name__ == '__main__':
    #run_clock()
    metronome()
