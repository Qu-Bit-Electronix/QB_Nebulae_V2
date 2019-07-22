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
Get messages from an scsynth server.
"""

import sys
import threading
import traceback
import socket
import tools


class Listener(threading.Thread):

    _timeout = 1

    def __init__(self, sock):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.callbacks = {}
        self._running = False
        self.socket = sock

    def register(self, key, callback):
        """ Register for key == None to receive all messages. """
        if not key in self.callbacks:
            self.callbacks[key] = []
        self.callbacks[key].append(callback)
        
    def quit(self, wait=False):
        self._running = False
        if wait:
            self.join(2)

    def _key(self, msg):
        """ defines how messages are identified. """
        return msg[0]

    def try_get(self):
        try:
            data, addr = self.socket.recvfrom(2**13)
            if data:
                return tools.decode(data)
            else:
                return None
        except socket.timeout:
            return None

    def run(self):
        self._running = True
        self.socket.settimeout(.5)
        try:
            while self._running:
                msg = self.try_get()
                if msg:
                    key = self._key(msg)
                    for cb in self.callbacks.get(None, []):
                        cb(msg)
                    for cb in self.callbacks.get(key, []):
                        cb(msg)
        except:
            sys.stderr.write('EXCEPTION IN LISTENER THREAD:\n')
            traceback.print_exc()


if __name__ == '__main__':
    
    PORT = 57110
    
    def print_message(msg):
        print 'GOT MESSAGE: %s' % msg
        
    listener = Listener(PORT)
    listener.register(None, print_message)

    print "Listening for messages, press enter to quit."
    listener.start()
    sys.stdin.read(1)
    listener.quit()
    listener.join()

