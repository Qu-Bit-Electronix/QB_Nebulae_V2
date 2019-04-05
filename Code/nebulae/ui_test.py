import ctcsound
import ui
import conductor
import controlhandler as ch

def display_encoder_data(interface):
    if interface.get_delta("pitch") != 0:
        print("rotate pitch %d" % interface.get_delta("pitch"))
    elif interface.get_delta("speed") != 0:
        print("rotate speed %d" % interface.get_delta("speed"))
    elif interface.clicked_pitch() == 1:
        print("PITCH CLICK!")
    elif interface.clicked_speed() == 1:
        print("SPEED CLICK!")
    else:
        pass

### Real Program begins here.
orc_handle = conductor.Conductor() # Initialize Audio File Tables and Csound Score/Orchestra
c = ctcsound.Csound()    # Create an instance of Csound
#optimize by making a set_options function that takes a list of options that can be set anywhere
c.setOption("-iadc:hw:0,0")
c.setOption("-odac:hw:0,0")  # Set option for Csound
c.setOption("-b512") # More Conservative buffer
c.setOption("-B1024") # More Conservative buffer
#c.setOption("-b128") # Liberal Buffer
#c.setOption("-B256") # Liberal Buffer
c.setOption("-+rtaudio=alsa") # Set option for Csound
#c.setOption("--sched")
c.setOption("-m7")  # Set option for Csound
c.compileOrc(orc_handle.curOrc)     # Compile Orchestra from String
c.readScore(orc_handle.curSco)     # Read in Score generated from notes 
c.start() # Start Csound

# Temp CSound csd playback
#c.compileCsd("tests/test.csd")
#c.start()

c_handle = ch.ControlHandler(c, orc_handle.numFiles()) # Create handler for all csound comm.
ui = ui.UserInterface(c_handle) # Create User Interface
pt = ctcsound.CsoundPerformanceThread(c.csound()) # Create CsoundPerformanceThread 
pt.play() # Begin Performing the Score in the perforamnce thread
c_handle.updateAll() # Update all values to ensure their at their initial state.

while (pt.status() == 0): # Run a loop to poll for messages, and handle the UI.
#while(True):
	c_handle.updateAll()
	ui.update()

#pt.stop()
#pt.join()
ui.cleanup()
print ("\nexited. . .\nGood Bye")
