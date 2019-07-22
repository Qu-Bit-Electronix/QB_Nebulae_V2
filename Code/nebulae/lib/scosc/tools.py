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
supercollider-specific OSC functions.
"""

import time
import math
import struct
import OSC
import osctools


class OSCMessage(object):
    """Builds OSC message how supercollider wants them
      
       Algo: build messages one at a time and throw in a list 
       don't build first message's tag, build all others' tags 
       (ints, strings, etc.)
       fill out the tag bytes to work % 4
       build the network message in binary
       
       (first OSCArgument(message)[1] +
       OSCArgument(tags(not First message)) +
       rest OSCArgument(message)[1])

       Use getBinary() for raw data.
       """
    def __init__(self):
        self.typetags = ","
        self.message  = ""
        self.messages = []
       
    def setMessage(self, message):
        self.message = message

    def setTypetags(self, typetags):
        self.typetags = typetags
        
    def clear(self):
        self.clearData()

    def clearData(self):
        self.typetags = ","
        self.message  = ""
        self.messages = []

    def append(self, argument, typehint = None):
        """Appends data to the message, updating the typetags based on
        the argument's type.  If the argument is a blob (counted string)
        pass in 'b' as typehint.
        """
        if typehint == 'b':
           binary = OSC.OSCBlob(argument)
        else:
           binary = OSC.OSCArgument(argument)
        if len(self.messages) != 0: 
           self.typetags = self.typetags + binary[0]
        self.messages.append(binary[1])

    def rawAppend(self, data):
        """Appends raw data to the message.  Use append()."""
        self.message = self.message + data
        #print "rawAppend changed self.message to %s"%str(self.message)

    def getBinary(self):
        """Returns the binary message (so far) with typetags."""
        typetags = OSC.OSCArgument(self.typetags)[1]
        if len(self.messages) == 1:
            
            return self.messages[0] + OSC.OSCArgument(self.typetags)[1]
            # Commands of length one need the first typetag
        elif len(self.messages) == 0:
            pass
        else:
            outMessage = self.messages[0] + typetags
            restOfEm = self.messages[1:]
            for eachMessage in restOfEm:
                outMessage += eachMessage
            return outMessage

    def __repr__(self):
        return self.getBinary()


JAN_1970 = 2208988800L
SECS_TO_PICOS = 4294967296L
def abs_to_timestamp(abs):
    """ since 1970 => since 1900 64b OSC """
    sec_1970 = long(abs)
    sec_1900 = sec_1970 + JAN_1970

    sec_frac = float(abs - sec_1970)
    picos = long(sec_frac * SECS_TO_PICOS)

    total_picos = (abs + JAN_1970) * SECS_TO_PICOS
    return struct.pack('!LL', sec_1900, picos)


def build_bundle(abs, messages):
    """ abs is floating point seconds since 1970.
    Abs should be in osc format for high precision, but this is easy.
    """
    oscmessage = OSCMessage()
    bundle_bin = osctools.convertStringToOSCBinary('#bundle')

    if abs <= time.time():
        timestamp = abs_to_timestamp(1L) # do it NOW
    else:
        timestamp = abs_to_timestamp(abs)
    bundle_bin += timestamp

    for message in messages:
        oscmessage.clearData()
        for data_guy in message:
            if type(data_guy) == type([]):
                oscmessage.append(argument = data_guy[0],
                                  typehint = data_guy[1])
            else:
                oscmessage.append(data_guy)
            bin = oscmessage.getBinary()
            bin_len = osctools.lengthOfMsg(bin)
        bundle_bin += (osctools.convertIntToNetworkInt(bin_len) + bin)

    return bundle_bin


def decode(data):
    """Converts a typetagged OSC message to a Python list.
    modified for supercollider-specific messages.
    """
    table = { "i":OSC.readInt,
              "f":OSC.readFloat,
              "s":OSC.readString,
              "b":OSC.readBlob,
              "d":OSC.readDouble}
    decoded = []
    address,  rest = OSC.readString(data)
    typetags = ""
    
    if address == "#bundle":
        time, rest = OSC.readLong(rest)
        decoded.append(address)
        decoded.append(time)
        while len(rest)>0:
            length, rest = OSC.readInt(rest)
            decoded.append(OSC.decodeOSC(rest[:length]))
            rest = rest[length:]
          
    elif len(rest) > 0:
        typetags, rest = OSC.readString(rest)
        
        decoded.append(address)
        decoded.append(typetags)
        if(typetags[0] == ","):
            for tag in typetags[1:]:
               try:
                   value, rest = table[tag](rest)
                   decoded.append(value)
               except:
                   print "%s probably not in tags list" %tag
                   print "check scOSCMessage.py - def decodeSCOSC():"
        else:
            print "Oops, typetag lacks the magic ,"
    try:
        returnList = [decoded[0]]
    except IndexError:
        returnList = []
    try:
        oldRtnList = returnList
        returnList.extend(decoded[2:])
    except IndexError:
        returnList = oldRtnList
    return returnList
   

def print_message(msg):
    print msg
