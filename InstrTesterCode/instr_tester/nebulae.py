#!/usr/bin/python
# Main Nebulae Source File
import ctcsound
import controlhandler as ch
import conductor
#import ui
import time
import threading
import sys
from Tkinter import *


if len(sys.argv) > 1:
	#Take argument from commandline
	instr = sys.argv[1]
else:
	instr = "a_granularlooper"


orc_handle = conductor.Conductor() # Initialize Audio File Tables and Csound Score/Orchestra
orc_handle.generate_orc(instr, "factory")
configData = orc_handle.getConfigDict()
c = ctcsound.Csound()    # Create an instance of Csound
c.setOption("-iadc") # Get this back in the game for local
c.setOption("-odac")  # Set option for Csound
c.setOption("-b1024") # More Conservative buffer
c.setOption("-B2048") # More Conservative buffer
#c.setOption("-b128") # Liberal Buffer
#c.setOption("-B256") # Liberal Buffer
#c.setOption("-+rtaudio=alsa") # Set option for Csound
#c.setOption("--sched")
c.setOption("-m7")  # Set option for Csound
c.compileOrc(orc_handle.curOrc)     # Compile Orchestra from String
c.readScore(orc_handle.curSco)     # Read in Score generated from notes 
c.start() # Start Csound

c_handle = ch.ControlHandler(c, orc_handle.numFiles(), configData) # Create handler for all csound comm.
#ui = ui.UserInterface(c_handle) # Create User Interface
pt = ctcsound.CsoundPerformanceThread(c.csound()) # Create CsoundPerformanceThread 
pt.play() # Begin Performing the Score in the perforamnce thread
c_handle.updateAll() # Update all values to ensure their at their initial state.

## Abstract these classes away when possible.
class Position(object):
    def __init__(self, row, column):
        self.row = row
        self.column = column

class SliderWrapper(object):
    def __init__(self, canvas, csound, channelName, position):
        tick_size = 1.0/4096.0
        self.name = channelName
        self.mode = 0
        self.slider = Scale(canvas, from_=0.0, to=1.0, resolution=tick_size, command=self.update, label=self.name)
        self.slider.grid(row=position.row,column=position.column)
        self.slider.set(c_handle.getValue(self.name))

    def update(self, dval):
        val = self.slider.get()
        if self.mode == 0:
            c_handle.channeldict[self.name].setValue(val)
        else:
            c_handle.altchanneldict[self.name+"_alt"].setValue(val)

    def setMode(self, val):
        if val == 0:
            self.mode = 0
            self.slider.set(c_handle.getValue(self.name))
        else:
            self.mode = 1
            self.slider.set(c_handle.getAltValue(self.name+"_alt"))

class Application(Frame):
    def __init__(self, master=None):
        master.title("Nebulae Instr Tester")
        self.items = []
        self.notes = []
        Frame.__init__(self,master,width=1000,height=1000)
        self.grid()
        self.createUI()
        self.master.protocol("WM_DELETE_WINDOW",self.quit)

    def updateMode(self):
        val = self.secondarySwitchState.get()
        for u in self.updaters:
            self.updaters[u].setMode(val)

    def createUI(self):
        self.size = 600
        self.canvas = Canvas(self, height=self.size, width=self.size)
        self.canvas.grid(row=0, column=0)
        self.slider_names = ["start", "size", "blend", "density", "overlap", "speed", "pitch", "window"]
        self.slider_positions = {
            "start":Position(1, 1),
            "speed":Position(1, 3),
            "size":Position(1, 5),
            "density":Position(2, 1),
            "pitch":Position(2, 3),
            "overlap":Position(2, 5),
            "blend":Position(3, 2),
            "window":Position(3, 4)
        }
        # Secondary Switch
        self.secondarySwitchState = IntVar()
        self.secondarySwitchButton = Checkbutton(self.canvas, text="Secondary", var=self.secondarySwitchState, command=self.handleSecondaryState)
        self.secondarySwitchButton.grid(row=3, column=3)
        # Generic Controls
        self.updaters = {}
        for name in self.slider_names:
            self.updaters[name] = SliderWrapper(self.canvas, c, name, self.slider_positions[name])
        # Record
        self.recordButtonState = IntVar()
        self.recordButton = Checkbutton(self.canvas, text="Record", var=self.recordButtonState, command=self.handleRecord)
        self.recordButton.grid(row=4,column=1)
        # Next
        self.nextButton = Button(self.canvas, text="Next", command=self.handleNext)
        self.nextButton.grid(row=4,column=2)
        # Source
        self.sourceButtonState = IntVar()
        self.sourceButton = Checkbutton(self.canvas, text="Source", var=self.sourceButtonState, command=self.handleSource)
        self.sourceButton.grid(row=4,column=3)
        # Reset
        self.resetButton = Button(self.canvas, text="Reset", command=self.handleReset)
        self.resetButton.grid(row=4,column=4)
        # Freeze
        self.freezeButtonState = IntVar()
        self.freezeButton = Checkbutton(self.canvas, text="Freeze", var=self.freezeButtonState, command=self.handleFreeze)
        self.freezeButton.grid(row=4,column=5)


    def updateControl(self, name):
        print "control: " + name
        if self.secondarySwitchState.get() == 0:
            try:
                self.updaters[name].update()
            except KeyError:
                print "key: " + str(name) + " is not a part of the updaters"
        else:
            try:
                self.updaters[name].update_alt()
            except KeyError:
                print "key: " + str(name) + " is not a part of the updaters"
        #c_handle.updateAll()
        
    def updateControls(self, val):
        #self.startUpdater.update()
        #self.sizeUpdater.update()
        #self.blendUpdater.update()
        #self.densityUpdater.update()
        #self.overlapUpdater.update()
        #self.windowUpdater.update()
        #self.speedUpdater.update()
        #self.pitchUpdater.update()
        for s in self.slider_names:
            self.updaters[s].update() 
        #c_handle.updateAll()

    def handleFreeze(self):
        print "Handling Freeze!"
        c_handle.channeldict["freeze"].setValue(self.freezeButtonState.get())
        c_handle.updateAll()

    def handleRecord(self):
        print "Handling Record!"
        c_handle.channeldict["record"].setValue(self.recordButtonState.get())
        c_handle.updateAll()

    def handleReset(self):
        print "Handling Reset!"
        c_handle.channeldict["reset"].setValue(1.0)
        #c_handle.updateAll()
        self.master.after(50, self.clearReset())
        #c_handle.channeldict["reset"].setValue(0)

    def clearReset(self):
        print "Clearing Reset"
        time.sleep(.05)
        c_handle.channeldict["reset"].setValue(0.0)
        #c_handle.updateAll()

    def handleSecondaryState(self):
        print "secondary state: " + str(self.secondarySwitchState.get())
        if self.secondarySwitchState.get() == 0:
            print "Switching to Normal Controls."
        else:
            print "Switching to Secondary Controls."
        self.updateMode() 

    def handleNext(self):
        print "Handling Next!"
        cur_file = c_handle.getValue("file")
        cur_file += 1
        if cur_file >= c_handle.numFiles:
            cur_file = 0
        c_handle.channeldict["file"].setValue(cur_file)
        #c_handle.updateAll()
        print "Current file index: " + str(cur_file)

    def handleSource(self):
        print "Handling Source!"
        c_handle.channeldict["source"].setValue(self.sourceButtonState.get())
        #c_handle.updateAll()

    def quit(self):
        self.master.destroy()
        pt.stop()
        pt.join()

app = Application(Tk())
app.mainloop()
c.stop
del c
