# Import SPI library (for hardware SPI) and MCP3008 library.
#import Adafruit_#GPIO.SPI as SPI
#import RPi.#GPIO as #GPIO
import ctcsound
#import switch as libSwitch
#import shiftregister as libSR
import control
import os
#import settings
import time
#import Adafruit_MCP3008

# Defines for Button/Gate Types
BUTTON_GATE_GPIO = 0
BUTTON_SR_GATE_GPIO = 1
BUTTON_GATE_SR = 2
BUTTON_GPIO_GATE_SR = 3
BUTTON_GPIO_GATE_NONE = 4
BUTTON_SR_GATE_NONE = 5

FREEZE_GATE_PIN = 4
RESET_GATE_PIN = 25
NEXT_GATE_PIN = 23
RECORD_GATE_PIN = 24


# Main Class. Holds all control.ControlChannels
class ControlHandler(object):
    def __init__(self, csound, numberFiles, configData):
        self.csound = csound # Share csound instance with object
        #GPIO.setmode(#GPIO.BCM) # init #GPIO
        #GPIO.setwarnings(False) # silence #GPIO warnings (this is probably not the best.)
        self.eol_pin = 16
        self.eol_state = False
        #GPIO.setup(self.eol_pin, #GPIO.OUT)
        #self.shiftReg = libSR.ShiftRegister()
        self.numFiles = numberFiles
        self.control_mode = "normal"
        self.configData = configData
        self.in_ticks = 23
        self.modeChangeControl = None
        #self.settings = settings.SettingManager()
        #self.settings.read()

        # Set Defaults/Read Config
        digitalControlList = [
            "reset", "freeze", "source", "record", "file", "recordstate",
            "reset_alt", "freeze_alt", "source_alt", "record_alt", "file_alt"
        ]
        self.defaultConfig = dict()
        self.populateDefaultConfig()
        digitalConfig = dict()
        for ctrl in digitalControlList:
            if self.configData.has_key(ctrl):
                digitalConfig[ctrl] = self.configData.get(ctrl)
            else:
                digitalConfig[ctrl] = self.defaultConfig.get(ctrl)
        self.channels = [control.ControlChannel(self.csound, "speed", 0.25, "static"),
                        control.ControlChannel(self.csound, "pitch", 0.5, "static"),
                        control.ControlChannel(self.csound, "start", 0.0, "static"),
                        control.ControlChannel(self.csound, "size", 1.0, "static"),
                        control.ControlChannel(self.csound, "mix", 0.0,"static"),
                        control.ControlChannel(self.csound, "density", 0.001, "static"),
                        control.ControlChannel(self.csound, "overlap", 0.0012, "static"),
                        control.ControlChannel(self.csound, "degrade", 1.0, "static"),
                        control.ControlChannel(self.csound, "file", 0, "static"),
                        control.ControlChannel(self.csound, "reset", 0, "static"),
                        control.ControlChannel(self.csound, "freeze", 0, "static"),
                        control.ControlChannel(self.csound, "source", 0, "static"),
                        control.ControlChannel(self.csound, "record", 0, "static"),
                        control.ControlChannel(self.csound, "recordstate", 0, "static")]

        self.altchannels = [control.ControlChannel(self.csound, "speed", 0.25, "static"),
                        control.ControlChannel(self.csound, "pitch_alt", 0.5, "static"),
                        control.ControlChannel(self.csound, "start_alt", 0.0, "static"),
                        control.ControlChannel(self.csound, "size_alt", 1.0, "static"),
                        control.ControlChannel(self.csound, "mix_alt", 0.0,"static"),
                        control.ControlChannel(self.csound, "density_alt", 0.000, "static"),
                        control.ControlChannel(self.csound, "overlap_alt", 0.0012, "static"),
                        control.ControlChannel(self.csound, "degrade_alt", 0.5, "static"),
                        control.ControlChannel(self.csound, "file_alt", 0, "static"),
                        control.ControlChannel(self.csound, "reset_alt", 0, "static"),
                        control.ControlChannel(self.csound, "freeze_alt", 0, "static"),
                        control.ControlChannel(self.csound, "source_alt", 0, "static"),
                        control.ControlChannel(self.csound, "record_alt", 0, "static")]
        self.channeldict = {}
        for chn in self.channels:
            self.channeldict[chn.name] = chn

        self.altchanneldict = {}
        for chn in self.altchannels:
            self.altchanneldict[chn.name] = chn

        # The Exit instrmode channel, is probably fine to leave for good, 
        # but the exit_secondarymode channel should be absorbed into the altchannels list
        #self.exit_instrmode_chn = control.control.ControlChannel(self.csound, "exit", 0, "digital",data_channel=BUTTON_GATE_SR, sr=self.shiftReg, gate_pin=libSR.PIN_SOURCE_GATE,button_pin=libSR.PIN_SOURCE, longtouch_cb=self.enterNormalMode)

#        self.exit_secondarymode_chn = control.control.ControlChannel(self.csound, "record", 0, "digital",data_channel=BUTTON_SR_GATE_#GPIO, sr=self.shiftReg, gate_pin=RECORD_GATE_PIN,button_pin=libSR.PIN_RECORD, longtouch_cb=self.enterNormalMode)
        ## Clean this stuff up.
        self.now = int(round(time.time() * 1000))
        self.instr_sel_idx = 0
        self.eol_comm = control.CommChannel(self.csound, "eol")
        self.size_status_comm = control.CommChannel(self.csound, "sizestatus")
        self.eol_gate_timer = 0
        self.reset_led_pin = 12
        #GPIO.setup(self.reset_led_pin, #GPIO.OUT)
        self.channeldict["recordstate"].setIgnoreGate(True)
        #for chn in self.channels:
           # if self.settings.hasSetting(chn.name):
           #     chn.setValue(float(self.settings.load(chn.name)))
           #     chn.update()
        #self.enterSecondaryMode()
        #for chn in self.altchannels:
        #    if self.settings.hasSetting(chn.name):
        #        chn.setValue(float(self.settings.load(chn.name)))
        #        chn.update()
        #self.enterNormalMode()
    



    # Generic Global Control Functions
    def setValue(self, name, value):
        self.channeldict[name].setValue(value)

    def setAltValue(self, name, value):
        self.altchanneldict[name].setValue(value)

    def getValue(self, name):
        return self.channeldict[name].getValue()

    def getAltValue(self, name):
        return self.altchanneldict[name].getValue()

    def getStaticVal(self, name):
        return self.channeldict[name].getStaticVal()

    def getInstrValue(self, name):
        return self.instrchanneldict[name].getValue()
    
    def getInstrSelIdx(self):
        return self.instr_sel_idx

    def updateChannel(self, name):
        self.channeldict[name].update()

    def updateAltChannel(self, name):
        self.altchanneldict[name].update()

    def mode(self):
        return self.control_mode
    
    def enterNormalMode(self):
        print "entering normal"
        if self.modeChangeControl is not None:
            self.channeldict[self.modeChangeControl].setIgnoreNextButton()
        if self.control_mode == "secondary controls":
            self.resistSecondarySettings()
        #self.settings.update(self.now)
        #self.settings.write()
        self.control_mode = "normal"
    
    def enterSecondaryMode(self):
        self.modeChangeControl = "file"
        self.altchanneldict[self.modeChangeControl + "_alt"].setIgnoreNextButton()
        if self.control_mode == "normal":
            print "entering secondary"
            self.resistNormalSettings() 
            self.control_mode = "secondary controls"
        #self.settings.update(self.now)
        #self.settings.write()

    def enterInstrSelMode(self):
        self.modeChangeControl = "source"
        self.instrchanneldict[self.modeChangeControl + "_instr"].setIgnoreNextButton()
        if self.control_mode == "normal":
            print "entering instr selector"
            self.control_mode = "instr selector"

    def resistNormalSettings(self):
        for i in range(0, 8):
            self.altchannels[i].setModeChangeValue(self.channels[i].getPotValue())
         

    def resistSecondarySettings(self):
        for i in range(0, 8):
            self.channels[i].setModeChangeValue(self.altchannels[i].getPotValue())

    def populateDefaultConfig(self):
        self.defaultConfig["reset"] = ["triggered", "rising"]
        self.defaultConfig["freeze"] = ["latching", "rising"]
        self.defaultConfig["source"] = ["latching", "falling"]
        self.defaultConfig["file"] = ["incremental", "falling"]
        self.defaultConfig["record"] = ["latching", "falling"]
        self.defaultConfig["recordstate"] = ["momentary", "rising"]
        self.defaultConfig["reset_alt"] = ["triggered", "rising"]
        self.defaultConfig["freeze_alt"] = ["latching", "rising"]
        self.defaultConfig["source_alt"] = ["latching", "falling"]
        self.defaultConfig["file_alt"] = ["incremental", "falling"]
        self.defaultConfig["record_alt"] = ["latching", "falling"]
        self.defaultConfig["ksmps"] = ["128"]
        self.defaultConfig["sr"] = ["44100"]

    def restoreAltToDefault(self):
        self.altchanneldict["speed_alt"].setValue(1.0)
        self.altchanneldict["pitch_alt"].setValue(0.0)
        self.altchanneldict["start_alt"].setValue(0.0)
        self.altchanneldict["size_alt"].setValue(0.0)
        self.altchanneldict["mix_alt"].setValue(0.0)
        self.altchanneldict["density_alt"].setValue(0.0)
        self.altchanneldict["overlap_alt"].setValue(0.0)
        self.altchanneldict["degrade_alt"].setValue(0.5)
        self.altchanneldict["reset_alt"].setValue(0.0)
        self.altchanneldict["freeze_alt"].setValue(0.0)
        self.altchanneldict["source_alt"].setValue(0.0)
        self.altchanneldict["record_alt"].setValue(0.0)
        self.altchanneldict["file_alt"].setValue(0.0)

    def setInputLevel(self, scalar):
        tick = scalar
        prev_ticks = self.in_ticks
        self.in_ticks = tick
        if prev_ticks != self.in_ticks:
            cmd = 'amixer set \'Capture\' ' + str(tick)
            os.system(cmd)

    def handleEndOfLoop(self):
        self.eol_comm.update()
        self.size_status_comm.update()
        if self.size_status_comm.getState() == 0:
            if self.eol_comm.getState() == 1:
                self.eol_comm.clearState()
                #GPIO.output(self.eol_pin, False)
                if self.control_mode == "normal": 
                    pass
                    #GPIO.output(self.reset_led_pin, False)
                self.eol_gate_timer = 0
                self.eol_state = True
            if self.eol_state is True:
                self.eol_gate_timer += 1
                if self.eol_gate_timer > 2:
                   #GPIO.output(self.eol_pin, True) 
                   if self.control_mode == "normal":
                      #GPIO.output(self.reset_led_pin, True) 
                      pass
                   self.eol_state = False
        #else:
          
            #GPIO.output(self.eol_pin, True)
            #GPIO.output(self.reset_led_pin, False)

    def updateAll(self): 
        ##GPIO.output(self.eol_pin, False)
        self.now = int(round(time.time() * 1000))
        #self.shiftReg.update()
        self.handleEndOfLoop()
        #self.printAllControls()
        if self.control_mode == "secondary controls":
            for chn in self.altchannels:
                chn.update()
                #self.settings.save(chn.name, chn.getValue())
            for chn in self.channels:
                chn.setIgnoreHID(True)
                chn.update()
            self.channeldict["file"].input.setIncOrder(self.altchanneldict["file_alt"].getValue()) 
            in_scalar = self.altchanneldict["speed_alt"].getValue()
            self.setInputLevel(in_scalar)
            if self.altchanneldict["reset_alt"].curVal == True:
              print "Restoring Defaults!"
              self.restoreAltToDefault()
              self.enterNormalMode()
        elif self.control_mode == "instr selector":
            #self.exit_instrmode_chn.update()
            for idx, chn in enumerate(self.instr_sel_controls):
                chn.update()
                if chn.getValue() == 1:
                   self.instr_sel_idx = idx
        else: #includes "normal"
            self.channeldict["recordstate"].update()
            recordstate = self.channeldict["recordstate"].getValue()
            for chn in self.channels:
                if chn.name != "recordstate":
                    #self.settings.save(chn.name, chn.getValue())
                    chn.setIgnoreGate(recordstate)
                    chn.setIgnoreHID(False)
                    chn.update()
                if chn.source == "digital" and chn.name != "record" and chn.name != "recordstate":
                    if recordstate == 1 or recordstate == True:
                        if chn.hasChanged() == True:
                            print "channel: " + chn.name + " has changed."
                            self.channeldict["record"].setIgnoreNextButton()
                            
    def printAllControls(self):
        line = "############################\n"
        line += "Primary Channels:"
        for i,chn in enumerate(self.channels):
            if i % 4 == 0:
                line +="\n"
            line += chn.name + ": " + str(chn.getValue()) + "\t"
        line += "\nSecondary Channels:"
        for i,chn in enumerate(self.altchannels):
            if i % 4 == 0:
                line += "\n"
            line += chn.name + ": " + str(chn.getValue()) + "\t"
        line += "\n############################\n"

        print line

        
        ##GPIO.output(self.eol_pin, True)
