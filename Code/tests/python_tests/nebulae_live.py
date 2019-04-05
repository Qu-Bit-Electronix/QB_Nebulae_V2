import csnd6
# Import SPI library (for hardware SPI) and MCP3008 library.
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
from random import randint, random
import time
# For Directory Searching
import glob
# Hardware SPI configuration:
SPI_PORT   = 0
SPI_DEVICE = 0


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

class InputData(object):
    def __init__(self, channel):
        self.curVal = 0.0
        self.channel = channel
        self.mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))

    def getValue(self):
        self.curVal = (((self.mcp.read_adc(self.channel)) / 1023.0) + 0.01) * 4;
        return self.curVal

class StoredFiles(object):
		def __init__(self):
				self.reset()
				self.scanfiles()

		def reset(self):
				self.numFiles = 0
				self.files = []

		def scanfiles(self):
				mypath = "../"
				self.files = glob.glob("../*.wav")

###############################

# Our Orchestra for our project
orc = """
sr=44100
ksmps=64
nchnls=2
0dbfs=1
instr 1
ainl, ainr inch 1, 2
outs ainl, ainr
endin"""

inputFiles = StoredFiles()
inputFiles.reset()
inputFiles.scanfiles()

for f in inputFiles.files:
		print f

c = csnd6.Csound()    # create an instance of Csound
c.SetOption("-iadc")
c.SetOption("-odac")  # Set option for Csound
c.SetOption("-b 64")
c.SetOption("-B 128")
c.SetOption("-+rtaudio=alsa") # Set option for Csound
c.SetOption("--realtime")
c.SetOption("--sched")
c.SetOption("-m7")  # Set option for Csound
c.CompileOrc(orc)     # Compile Orchestra from String

# Set the Instrument to Play for 60 seconds. Change this to infinite later.
sco = "f0 $INF\n" + "i1 0 -10\n"
# Set the ftables based on the files within the specified directory.
#fsco = "f 1 0 0 1 \"" + inputFiles.files[0] + "\" 0 0 0\n" #sco = isco + fsco


c.ReadScore(sco)     # Read in Score generated from notes 

c.Start()             # When compiling from strings, this call is necessary before doing any performing

# Create a set of ChannelUpdaters
#channels = [ChannelUpdater(c, "amp", RandomLine(-2.0, 2.0)),
#            ChannelUpdater(c, "freq", RandomLine(0.6, 8.0)),
#            ChannelUpdater(c, "resonance", RandomLine(0.4, .3))]
#freq_ctrl = InputData(0)
#amp_ctrl = InputData(1)
#res_ctrl = InputData(2)
freq_ctrl = InputData(1)
amp_ctrl = InputData(0)
res_ctrl = RandomLine(0.6, 8.0)

channels = [ChannelUpdater(c, "amp", freq_ctrl),
			ChannelUpdater(c, "freq", amp_ctrl),
			ChannelUpdater(c, "resonance", res_ctrl)]

# Initialize all Channel Values
for chn in channels:
    chn.update()

while (c.PerformKsmps() == 0):
    for chn in channels:   # update all channel values
        chn.update()

c.Stop()



