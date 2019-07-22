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
Brain folding fuel.

Live timeline editor
 - pattern
  \_ notes
    \_ on, off events

pattern/notes

EVENT POOL
current time
end time
expiration
music time - repr?
control window
play window

NOTE POOL
id pool
"""

import container


class Synth(container.DictProxy):
    """ a dict of values, set once per note. """
    
    name = None
    node = None

    def __init__(self):
        container.DictProxy.__init__(self)

    def __repr__(self):
        s = container.DictProxy.__repr__(self)
        return "<%s name=\'%s\', node=\'%s\', %s>" % (self.__class__.__name__,
                                                      self.name, self.node,
                                                      s)
    def __str__(self):
        return self.__repr__()

    def pitch(self, pitch):
        """ 0.0 < pitch < n
        nominal: 1.0
        """
        pass


class Effect(Synth):
    pass


class Player:
    """ manage synth and buffer ids for playing synths. """
    def __init__(self, server):
        self.server = server

    def route(self, synth, sid):
        if synth.node is None:
            action = 1
            node = 0
        else:
            action = 2
            node = synth.node
        return ['/s_new', synth.name, sid, action, node]

    def play(self, synth, start, stop):
        self.server.synthpool.check()
        sid = self.server.synthpool.get(stop + 5)
        msg = self.route(synth, sid)
        for key, value in synth.items():
            msg.extend([key, value])
        self.server.sendBundleAbs(start, [msg])
        self.server.sendBundleAbs(stop, [['/n_free', sid]])

    def play_rt(self, synth):
        """ """
        self.server.synthpool.check()
        sid = self.server.synthpool.get()
        msg = self.route(synth, sid)
        for key, value in synth.items():
            msg.extend([key, value])
        self.server.sendBundleAbs(-1, [msg])
        return sid
        
    def stop_rt(self, sid):
        """ """
        self.server.sendBundleAbs(-1, [['/n_free', sid]])
        self.server.synthpool.recycle(sid)


def main():
    import os
    import time
    import tempoclock
    import loader
    import server

    ctl = server.connect(spew=True)
    ctl.sendMsg('/dumpOSC', 1)

    SYNTHDEF_PATH = os.path.join(os.path.expanduser('~'),
                                 '.pksampler', 'synthdefs')
    SYNTHDEFS = ('JASStereoSamplePlayer.scsyndef',
                 'JASSine.scsyndef',
                 )
    for fname in SYNTHDEFS:
        ctl.sendMsg('/d_load', os.path.join(SYNTHDEF_PATH, fname))

    player = Player(ctl)
    ldr = loader.Loader(ctl)
    bid = ldr.load('/Users/patrick/.pksampler/clicks/click_1.wav')

    clock = tempoclock.TempoClock(140.0)

    beats = [clock.spb() * i for i in range(100)]
    now = time.time() + 1
    freqs = [440, 550, 220, 200, 460]
    synth = Synth()
    synth.name = 'JASSine'
    for seconds in beats:
        abs = now + seconds
        freqs = freqs[1:] + freqs[:1]
        synth['freq'] = freqs[0]
        player.play(synth, abs, abs + 1)


if __name__ == '__main__':
    main()
