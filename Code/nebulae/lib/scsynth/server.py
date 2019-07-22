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
High level Server class, like the one in sclang.
"""

import os
import socket
import scosc
import process
import pool


class _Server(scosc.Controller):
    """ Strictly for convenince. This is poorly thought-out and so
    probably bad design.
    """
    
    proc = None

    def __init__(self, addr, verbose=False):
        scosc.Controller.__init__(self, addr, verbose)
        self.audiobuspool = pool.IntPool(29)
        self.controlbuspool = pool.IntPool(0)
        self.synthpool = pool.IntPool(1000) 
        self.bufferpool = pool.IntPool(0)
        
    def quit(self):
        self.sendMsg('/quit')
        #self.receive('/done', '/fail')

    def kill(self):
        if self.proc:
            self.proc.kill()

    def ensure_dead(self):
        if self.proc and self.proc.isAlive():
            self.kill()


def connect(iphost='localhost', port=57110, verbose=False, spew=False):
    ip = socket.gethostbyname(iphost)
    s = _Server((ip, port), verbose)
    s.spew = spew
    #s.sendMsg('/status', 1)
    #s.receive('status.reply')
    return s


def start( #exe = 'scsynth', exedir = '/Applications/SuperCollider',
          port = 57110,
          #inputs = 2, outputs = 2, samplerate = 48000,
          verbose = False, spew = False,
          ) :
##    instance = process.start_local(exe, exedir, port,
##                                   inputs, outputs, samplerate, 
##                                   verbose,
##                                    )
    import time
    time.sleep(1)
    s = connect('127.0.0.1', port, verbose=verbose, spew=spew)
##    s.instance = 0 # instance
    return s

def startServer(
    exe = 'scsynth', exedir = '/Applications/SuperCollider',
    port = 57110,
    inputs = 2,
    outputs = 2,
    samplerate = 48000,
    verbose = False,
    spew = False,
          ) :

    instance = process.start_local(exe, exedir, port,
                                   inputs, outputs, samplerate, 
                                   verbose,
                                    )
    return instance


def test_start():
    import time
    s = start('scsynth', os.getcwd(), 2, 2, 48000)
    time.sleep(1)
    s.quit()

def test_connect():
    s = connect('127.0.0.1', 57110)
    s.quit()

if __name__ == '__main__':
    test_start()
    #test_connect()
