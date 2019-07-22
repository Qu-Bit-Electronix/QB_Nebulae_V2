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
import sys
import os
import time
import math
import struct
import OSC
import math

### F(n) defs for converting time to OTC network bytes
seconds1900To1970 = 2208988800L
# (70*365*24*60*60) + (17*24*60*60) 17 leap Years Holy crap...

# From the Supercollider source! ... (C) Daniel McCarthy
kSecondsToOSC  = 4294967296L # pow(2,32)/1
kMicrosToOSC = 4294.967296 # pow(2,32)/1e6
kNanosToOSC  = 4.294967296 # pow(2,32)/1e9
kOSCtoSecs = 2.328306436538696e-10  # 1/pow(2,32)
kOSCtoNanos  = 0.2328306436538696 # 1e9/pow(2,32)


def fractionalPart(floater):
   """Returns the Fractional part (_fractionalPart(1.5) == .5) of a
   number"""
   return(math.modf(float(floater))[0]) 
   # float conversion is there just in case I get an int or something
   
def fractionalPartToInt(floater):
   fpart = fractionalPart(floater)
   powersOfTen = len(str(fpart)) - 2
   return int(fpart * (10**powersOfTen))
   
def integerPart(floater): return(int(floater))

def byteLength(CommandBinary): # TO DO
   """returns the length in bytes of the command"""
   pass
   
def convertStringToOSCBinary(stringin): # from OSC.py.OSCArgument
   OSCstringLength = math.ceil((len(stringin)+1) / 4.0) * 4
   return(struct.pack(">%ds" % (OSCstringLength), stringin))
   
def convertIntToNetworkLongInt(longInt):
   return struct.pack('>Q', longInt)
   
def convertIntToNetworkInt(shortInt):
   return struct.pack('>i', shortInt)

def convertNetworkToLongInt(byteString):
   out = struct.unpack('>Q', byteString)
   return out[0]
   
def oscSecondFraction(fPartOfTime):
   return int((fPartOfTime)*(2**32))
   
def timeSince1970ToOscTime(timeSince1970):
   since1900 = timeSince1970 + seconds1900To1970
   return long(since1900 * kSecondsToOSC)
   
def currentOscTime():
   return(timeSince1970ToOscTime(time.time()))
   
def intervalToOscTime(interval, latency = 0):
   # in case I want to do network latency later
   return(timeSince1970ToOscTime(time.time() + interval - latency))

def lengthOfMsg(msg): # byte length of message
   return len(msg)

