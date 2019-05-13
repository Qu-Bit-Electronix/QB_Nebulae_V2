import csnd6
from random import randint, random
#from os import listdir
#from os.path import isfile, join
import glob


class RandomLine(object):
    def __init__(self, base, range):
        self.curVal = 0.0
        self.reset()
        self.base = base
        self.range = range

    def reset(self):
        self.dur = randint(256,512) 
        self.end = random() 
        self.slope = (self.end - self.curVal) / self.dur

    def getValue(self):
        self.dur -= 1
        if(self.dur < 0):
            self.reset()
        retVal = self.curVal
        self.curVal += self.slope
        return self.base + (self.range * retVal)


def createChannel(csound, channelName):
    chn = csnd6.CsoundMYFLTArray(1) 
    csound.GetChannelPtr(chn.GetPtr(), channelName, 
        csnd6.CSOUND_CONTROL_CHANNEL | csnd6.CSOUND_INPUT_CHANNEL) 
    return chn

class ChannelUpdater(object):
    def __init__(self, csound, channelName, updater):
        self.updater = updater
        self.channel = createChannel(csound, channelName)

    def update(self):
        self.channel.SetValue(0, self.updater.getValue())

class StoredFiles(object):
		def __init__(self):
				self.reset()
				self.scanfiles()

		def reset(self):
				self.numFiles = 0
				self.files = []

		def scanfiles(self):
				mypath = "../../audio/"
				self.files = glob.glob(mypath + "*.wav")

###############################

# Our Orchestra for our project
orc = """
sr=44100
ksmps=32
nchnls=2
0dbfs=1
instr 1
idur = 60
ilock = 0
ipitch chnget "freq"
itimescale chnget "amp"
iamp = 0.8
atime line 0, idur, idur*itimescale
asig mincer atime, iamp, ipitch, 1, ilock
outs asig, asig
endin"""

inputFiles = StoredFiles()
inputFiles.reset()
inputFiles.scanfiles()

for f in inputFiles.files:
		print f

c = csnd6.Csound()    # create an instance of Csound
c.SetOption("-odac")  # Set option for Csound
c.SetOption("-m7")  # Set option for Csound
c.CompileOrc(orc)     # Compile Orchestra from String

# Set the Instrument to Play for 60 seconds. Change this to infinite later.
isco = "i1 0 60\n"

# Set the ftables based on the files within the specified directory.
fsco = "f 1 0 0 1 \"" + inputFiles.files[0] + "\" 0 0 0\n"
sco = isco + fsco

c.ReadScore(sco)     # Read in Score generated from notes 

c.Start()             # When compiling from strings, this call is necessary before doing any performing

# Create a set of ChannelUpdaters
channels = [ChannelUpdater(c, "amp", RandomLine(-2.0, 2.0)),
            ChannelUpdater(c, "freq", RandomLine(0.6, 8.0)),
            ChannelUpdater(c, "resonance", RandomLine(0.4, .3))]

# Initialize all Channel Values
for chn in channels:
    chn.update()

while (c.PerformKsmps() == 0):
    for chn in channels:   # update all channel values
        chn.update()

c.Stop()



