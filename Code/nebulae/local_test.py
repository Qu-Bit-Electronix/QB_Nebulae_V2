import controlhandler as ch
import csnd6
import conductor

orc_handle = conductor.Conductor()

time = 0
c = csnd6.Csound()    # create an instance of Csound
#optimize by making a set_options function that takes a list of options that can be set anywhere
c.SetOption("-odac")  # Set option for Csound
#c.SetOption("-+rtaudio=alsa") # Set option for Csound
#c.SetOption("--sched")
c.SetOption("-m7")  # Set option for Csound
c.CompileOrc(orc_handle.curOrc)     # Compile Orchestra from String

c.ReadScore(orc_handle.curSco)     # Read in Score generated from notes 

c.Start()             # When compiling from strings, this call is necessary before doing any performing
while	(c.PerformKsmps() == 0):
	time += 1

c.stop()

#while	c.PerformKsmps() == 0
#perfThread = csnd6.CsoundPerformanceThread(c)
#while (c.PerformKsmps() == 0)
