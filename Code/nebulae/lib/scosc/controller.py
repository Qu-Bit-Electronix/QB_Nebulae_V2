#!/usr/bin/env python
#
#   Copyright (C) 2006 by Patrick Stinson and Jonathan Saggau             
#   patrickkidd@gmail.com   saggau@gmail.com                              
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
Control an sc server.
"""

import time
import socket
import Queue
import tools
import listener


class Controller:
    """ Communicates to an osc server.
    Refer to the OSC spec for method arguments.

    NOTE: A method like quitServer() that sends /quit should go in a
    'convenience' class, as this class focuses exclusively on
    primitive communication.
    """

    _timeout = 2

    def __init__(self, addr, verbose=True, spew=False):
        self.serverip, self.serverport = addr
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(self._timeout)

        self.incoming = Queue.Queue()
        self.listener = listener.Listener(self.socket)
        self.listener.register(None, self.incoming.put)
        if verbose:
            self.listener.register(None, tools.print_message)
        self.listener.start()
        self.spew = spew

    def __del__(self):
        self.listener.quit(wait=True)

    def _send(self, bin):
        self.socket.sendto(bin, (self.serverip, self.serverport))

    def sendMsg(self, *args):
        if self.spew:
            print args
        oscmessage = tools.OSCMessage()
        for arg in args:
            oscmessage.append(arg)
        self._send(oscmessage.getBinary())

    def sendBundle(self, fromnow, messages):
        if self.spew:
            print 'bundle:', fromnow
            for msg in messages:
                print '   ', tuple(msg)
        self.sendBundleAbs(time.time() + fromnow, messages)

    def sendBundleAbs(self, abs, messages):
        if self.spew:
            print 'bundle', abs
            for msg in messages:
                print '   ',tuple(msg)
        bin = tools.build_bundle(abs, messages)
        self._send(bin)

    def receive(self, *keys):
        """ Return the first message, or the first message that
        matches a key in keys.

        Should old messages expire and be removed somehow to avoid
        excessive cleanup here?
        """
        while True:
            try:
                msg = self.incoming.get(timeout=self._timeout)
                if not keys or msg[0] in keys:
                    return msg
            except Queue.Empty, e:
                raise IOError('timeout waiting for reply')
