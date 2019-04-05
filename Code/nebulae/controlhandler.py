# Import SPI library (for hardware SPI) and MCP3008 library.
import Adafruit_GPIO.SPI as SPI
import RPi.GPIO as GPIO
import ctcsound
import switch as libSwitch
import shiftregister as libSR
import control
import pdsender
import os
import settings
import time
import threading
import wavewriter
import numpy as np


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


# Main Class. Holds all ControlChannels
class ControlHandler(object):
    def __init__(self, csound, numberFiles, configData, instr='a_granularlooper', bank='factory'):
        self.csound = csound # Share csound instance with object
        GPIO.setmode(GPIO.BCM) # init GPIO
        GPIO.setwarnings(False) # silence GPIO warnings (this is probably not the best.)
        self.eol_pin = 16
        self.eol_state = False
        GPIO.setup(self.eol_pin, GPIO.OUT)
        self.shiftReg = libSR.ShiftRegister()
        self.numFiles = numberFiles
        self.control_mode = "normal"
        self.prev_control_mode = "normal"
        self.configData = configData
        self.in_ticks = 23
        self.modeChangeControl = None
        self.settings = settings.SettingManager(configData)
        self.settings.read()
        self.saveFlag = 0
        self.now = int(round(time.time() * 1000))
        self.pdSock = pdsender.PdSend()
        self.currentInstr = instr
        self.currentBank = bank
        self.static_file_idx = 0
        self.prep_mode_change = False
        self.prep_mode_change_time = self.now
        self.modeChangeValues = {}
        self.writer = wavewriter.WaveWriter() 
        self.writing_buffer = False
        self.buffer_failure = False
        self.performance_thread = None

        # Set Defaults/Read Config
        digitalControlList = [
            "reset", "freeze", "source", "record", "file", "filestate", "sourcegate",
            "reset_alt", "freeze_alt", "source_alt", "record_alt", "file_alt"
        ]
        self.defaultConfig = dict()
        self.populateDefaultConfig()
        digitalConfig = dict()
        for ctrl in digitalControlList:
            if self.configData is not None and self.configData.has_key(ctrl):
                digitalConfig[ctrl] = self.configData.get(ctrl)
            else:
                digitalConfig[ctrl] = self.defaultConfig.get(ctrl)
            #print "control: " + ctrl + " vals: " + str(digitalConfig[ctrl])

        self.channels = [
            control.ControlChannel(self.csound, "speed", self.settings.load("speed"), "hybrid", 1),
            control.ControlChannel(self.csound, "pitch", self.settings.load("pitch"), "hybrid", 4),
            control.ControlChannel(self.csound, "start", self.settings.load("start"), "analog", 0), 
            control.ControlChannel(self.csound, "size", self.settings.load("size"), "analog", 6),
            control.ControlChannel(self.csound, "blend",self.settings.load("blend"),"analog", 1, cvchn=3),
            control.ControlChannel(self.csound, "density", self.settings.load("density"), "analog", 2),
            control.ControlChannel(self.csound, "overlap", self.settings.load("overlap"), "analog", 7),
            control.ControlChannel(self.csound, "window", self.settings.load("window"), "analog", 5),
            control.ControlChannel(self.csound, "reset", 0, "digital",data_channel=BUTTON_SR_GATE_GPIO, sr=self.shiftReg, gate_pin=RESET_GATE_PIN,button_pin=libSR.PIN_RESET, config=digitalConfig.get("reset")),
            control.ControlChannel(self.csound, "freeze", self.settings.load("freeze"), "digital",data_channel=BUTTON_SR_GATE_GPIO, sr=self.shiftReg, gate_pin=FREEZE_GATE_PIN,button_pin=libSR.PIN_FREEZE, config=digitalConfig.get("freeze")),
            control.ControlChannel(self.csound, "record", self.settings.load("record"), "digital",data_channel=BUTTON_SR_GATE_GPIO, sr=self.shiftReg, gate_pin=RECORD_GATE_PIN,button_pin=libSR.PIN_RECORD, config=digitalConfig.get("record")),
            control.ControlChannel(self.csound, "file", self.settings.load("file"), "digital", data_channel=BUTTON_SR_GATE_GPIO, sr=self.shiftReg, gate_pin=NEXT_GATE_PIN,button_pin=libSR.PIN_NEXT,config=digitalConfig.get("file"),maximum=self.numFiles),
            control.ControlChannel(self.csound, "source", self.settings.load("source"), "digital",data_channel=BUTTON_GATE_SR, sr=self.shiftReg, gate_pin=libSR.PIN_SOURCE_GATE,button_pin=libSR.PIN_SOURCE, config=digitalConfig.get("source")),
            control.ControlChannel(self.csound, "filestate", 0, "digital",data_channel=BUTTON_SR_GATE_GPIO, sr=self.shiftReg, gate_pin=NEXT_GATE_PIN,button_pin=libSR.PIN_NEXT, config=digitalConfig.get("filestate")) ,
            control.ControlChannel(self.csound, "sourcegate", 0, "digital",data_channel=BUTTON_GATE_SR, sr=self.shiftReg, gate_pin=libSR.PIN_SOURCE_GATE,button_pin=libSR.PIN_SOURCE, config=digitalConfig.get("sourcegate")) ] 
        self.altchannels = [
            control.ControlChannel(self.csound, "speed_alt", self.settings.load("speed_alt"), "hybrid", -1, maximum=32),
            control.ControlChannel(self.csound, "pitch_alt", self.settings.load("pitch_alt"), "hybrid", -1),
            control.ControlChannel(self.csound, "start_alt", self.settings.load("start_alt"), "analog", 0, cvchn=-1), 
            control.ControlChannel(self.csound, "size_alt", self.settings.load("size_alt"), "analog", 6, cvchn=-1),
            control.ControlChannel(self.csound, "blend_alt", self.settings.load("blend_alt"),"analog", 1, cvchn=-1),
            control.ControlChannel(self.csound, "density_alt", self.settings.load("density_alt"), "analog", 2, cvchn=-1),
            control.ControlChannel(self.csound, "overlap_alt", self.settings.load("overlap_alt"), "analog", 7, cvchn=-1),
            control.ControlChannel(self.csound, "window_alt", self.settings.load("window_alt"), "analog", 5, cvchn=-1),
            control.ControlChannel(self.csound, "reset_alt", self.settings.load("reset_alt"), "digital",data_channel=BUTTON_SR_GATE_GPIO, sr=self.shiftReg, gate_pin=RESET_GATE_PIN,button_pin=libSR.PIN_RESET, config=digitalConfig.get("reset_alt")),
            control.ControlChannel(self.csound, "freeze_alt", self.settings.load("freeze_alt"), "digital",data_channel=BUTTON_SR_GATE_GPIO, sr=self.shiftReg, gate_pin=FREEZE_GATE_PIN,button_pin=libSR.PIN_FREEZE, config=digitalConfig.get("freeze_alt")),
            control.ControlChannel(self.csound, "source_alt", self.settings.load("source_alt"), "digital",data_channel=BUTTON_GATE_SR, sr=self.shiftReg, gate_pin=libSR.PIN_SOURCE_GATE,button_pin=libSR.PIN_SOURCE, config=digitalConfig.get("source_alt")),
            control.ControlChannel(self.csound, "record_alt", self.settings.load("record_alt"), "digital",data_channel=BUTTON_SR_GATE_GPIO, sr=self.shiftReg, gate_pin=RECORD_GATE_PIN,button_pin=libSR.PIN_RECORD, config=digitalConfig.get("record_alt")), 
            control.ControlChannel(self.csound, "file_alt", self.settings.load("file_alt"), "digital", data_channel=BUTTON_SR_GATE_GPIO, sr=self.shiftReg, gate_pin=NEXT_GATE_PIN,button_pin=libSR.PIN_NEXT,config=digitalConfig.get("file_alt"), maximum=3)
            ]

        self.instr_sel_controls = [
            control.ControlChannel(self.csound, "record_instr", 0, "digital",data_channel=BUTTON_SR_GATE_NONE, sr=self.shiftReg, button_pin=libSR.PIN_RECORD, config=["triggered", "falling"]),
            control.ControlChannel(self.csound, "file_instr", 0, "digital", data_channel=BUTTON_SR_GATE_NONE, sr=self.shiftReg, button_pin=libSR.PIN_NEXT,config=["triggered","falling"]),
            control.ControlChannel(self.csound, "source_instr", 0, "digital",data_channel=BUTTON_SR_GATE_NONE, sr=self.shiftReg, button_pin=libSR.PIN_SOURCE, config=["triggered","falling"]),
            control.ControlChannel(self.csound, "reset_instr", 0, "digital",data_channel=BUTTON_SR_GATE_NONE, sr=self.shiftReg, button_pin=libSR.PIN_RESET, config=["triggered", "falling"]),
            control.ControlChannel(self.csound, "freeze_instr", 0, "digital",data_channel=BUTTON_SR_GATE_NONE, sr=self.shiftReg, button_pin=libSR.PIN_FREEZE, config=["triggered","falling"])
            ]
        self.channeldict = {}
        for chn in self.channels:
            self.channeldict[chn.name] = chn

        self.altchanneldict = {}
        for chn in self.altchannels:
            self.altchanneldict[chn.name] = chn

        self.instrchanneldict = {}
        for chn in self.instr_sel_controls:
            self.instrchanneldict[chn.name] = chn

        self.editFunctionFlag = {}
        for chn in self.channels:
            if chn.source == "digital" and chn.name != "file" and chn.name != "filestate":
                self.editFunctionFlag[chn.name] = False

        self.sourceStateCtrl = control.ControlChannel(self.csound, "source_state", 0, "digital",data_channel=BUTTON_SR_GATE_NONE, sr=self.shiftReg, button_pin=libSR.PIN_SOURCE, config=["momentary","rising"], longtouch_cb=None)
        ## Clean this stuff up.
        self.instr_sel_idx = 0
        self.instr_sel_bank = "factory"
        self.instr_sel_offset = 0
        self.instr_sel_numfiles = 5
        self.eol_comm = control.CommChannel(self.csound, "eol")
        self.size_status_comm = control.CommChannel(self.csound, "sizestatus")
        self.record_status_comm = control.CommChannel(self.csound, "recordstatus")
        self.buffer_size_comm = control.CommChannel(self.csound, "bufferlength")
        self.eol_gate_timer = 0
        self.reset_led_pin = 12
        #GPIO.setup(self.reset_led_pin, GPIO.OUT)
        self.channeldict["filestate"].setIgnoreGate(True)
        self.channeldict["sourcegate"].setIgnoreHID(True)
        # Worker for writing audio file.
        #self.writeThread = threading.Thread(target=self.writeBufferToAudioFile())
        self.writeThread = threading.Thread(target=self.dummyThread())
        self.writeThread.start()
    


    # Pass Csound Performance Thread Pointer
    def setCsoundPerformanceThread(self, ptr):
        self.performance_thread = ptr

    # Generic Global Control Functions
    def setValue(self, name, value):
        self.channeldict[name].setValue(value)

    def setAltValue(self, name, value):
        self.altchanneldict[name].setValue(value)

    def getValue(self, name):
        return self.channeldict[name].getValue()

    def getAltValue(self, name):
        return self.altchanneldict[name].getValue()

    def getLEDValue(self, name):
        return self.channeldict[name].getLEDValue()

    def getAltLEDValue(self, name):
        return self.altchanneldict[name].getLEDValue()

    def getStaticVal(self, name):
        return self.channeldict[name].getStaticVal()

    def getAltStaticVal(self, name):
        return self.altchanneldict[name].getStaticVal()

    def getInstrValue(self, name):
        return self.instrchanneldict[name].getValue()

    def getInstrSelIdx(self):
        return self.instr_sel_idx

    def getInstrSelBank(self):
        return self.instr_sel_bank

    def getInstrSelOffset(self):
        return self.instr_sel_offset

    def setInstrSelIdx(self, idx):
        self.instr_sel_idx = idx

    def setInstrSelBank(self, bank):
        self.instr_sel_bank = bank

    def setInstrSelOffset(self, offset):
        self.instr_sel_offset = offset
    
    def setInstrSelNumFiles(self, numfiles):
        self.instr_sel_numfiles = numfiles

    def updateChannel(self, name):
        self.channeldict[name].update()

    def updateAltChannel(self, name):
        self.altchanneldict[name].update()

    def setCurrentInstr(self, name):
        self.currentInstr = name

    def mode(self):
        return self.control_mode
    
    def enterNormalMode(self):
        print "entering normal"
        for chn in self.channels:
            chn.muteCSound(False)
        if self.modeChangeControl is not None:
            self.channeldict[self.modeChangeControl].setIgnoreNextButton()
        if self.control_mode == "secondary controls":
            self.resistSecondarySettings()
        self.settings.update(self.now)
        self.settings.write()
        self.altchanneldict["source_alt"].setValue(0)
        self.prev_control_mode = self.control_mode
        self.control_mode = "normal"
        if self.pdSock.is_connected():
            self.pdSock.close()

    def enterPureDataMode(self):
        self.prev_control_mode = self.control_mode
        if self.modeChangeControl is not None:
            self.channeldict[self.modeChangeControl].setIgnoreNextButton()
        if self.control_mode == "secondary controls":
            self.resistSecondarySettings()
        for chn in self.channels:
            chn.muteCSound(True)
        if not self.pdSock.is_connected():
            print "Connecting to PD Socket"
            self.pdSock.connect()
        self.control_mode = "puredata"
    
    def enterSecondaryMode(self):
        #self.modeChangeControl = "pitch"
        #self.altchanneldict[self.modeChangeControl + "_alt"].setIgnoreNextButton()
        if self.control_mode == "normal" or self.control_mode == "puredata":
            print "entering secondary"
            self.resistNormalSettings() 
            if not self.pdSock.is_connected() and self.control_mode == "puredata":
                print "Connecting to PD Socket"
                self.pdSock.connect()
            self.prev_control_mode = self.control_mode
            self.control_mode = "secondary controls"
        for chn in self.channels:
            chn.setIgnoreHID(True)
        self.settings.update(self.now)
        self.settings.write()

    def enterInstrSelMode(self):
        #self.modeChangeControl = "speed"
        #self.instrchanneldict[self.modeChangeControl + "_instr"].setIgnoreNextButton()
        if self.control_mode == "normal" or self.control_mode == "puredata":
            print "entering instr selector"
            self.control_mode = "instr selector"
        self.settings.update(self.now)
        self.settings.write()
        for chn in self.channels:
            chn.muteCSound(True)

    def resistNormalSettings(self):
        for i in range(0, 8):
            #self.altchannels[i].setValue(self.altchannels[i].getPotValue())
            self.altchannels[i].setModeChangeValue(self.channels[i].getPotValue())
         

    def resistSecondarySettings(self):
        for i in range(0, 8):
            #self.channels[i].setValue(self.channels[i].getPotValue())
            self.channels[i].setModeChangeValue(self.channels[i].getPotValue())

    def populateDefaultConfig(self):
        if self.control_mode == "normal" or self.control_mode == "secondary controls":
            self.defaultConfig["reset"] = ["triggered", "rising"]
            self.defaultConfig["freeze"] = ["latching", "rising"]
            self.defaultConfig["source"] = ["latching", "falling"]
            self.defaultConfig["file"] = ["incremental", "falling"]
            self.defaultConfig["record"] = ["latching", "rising"]
            self.defaultConfig["filestate"] = ["momentary", "rising"]
            self.defaultConfig["reset_alt"] = ["triggered", "rising"]
            self.defaultConfig["freeze_alt"] = ["latching", "rising"]
            self.defaultConfig["source_alt"] = ["latching", "falling"]
            self.defaultConfig["file_alt"] = ["incremental", "falling"]
            self.defaultConfig["record_alt"] = ["latching", "falling"]
            self.defaultConfig["sourcegate"] = ["triggered", "rising"]
            self.defaultConfig["ksmps"] = ["128"]
            self.defaultConfig["sr"] = ["44100"]
        elif self.control_mode == "puredata":
            self.defaultConfig["reset"] = ["triggered", "rising"]
            self.defaultConfig["freeze"] = ["latching", "rising"]
            self.defaultConfig["source"] = ["latching", "falling"]
            self.defaultConfig["file"] = ["latching", "falling"]
            self.defaultConfig["record"] = ["latching", "rising"]
            self.defaultConfig["filestate"] = ["momentary", "rising"]
            self.defaultConfig["reset_alt"] = ["triggered", "rising"]
            self.defaultConfig["freeze_alt"] = ["latching", "rising"]
            self.defaultConfig["source_alt"] = ["latching", "falling"]
            self.defaultConfig["file_alt"] = ["incremental", "falling"]
            self.defaultConfig["record_alt"] = ["latching", "falling"]
            self.defaultConfig["sourcegate"] = ["triggered", "rising"]
            self.defaultConfig["ksmps"] = ["128"]
            self.defaultConfig["sr"] = ["44100"]
            

    def restoreAltToDefault(self):
        nowvals = dict()
        for name in self.altchanneldict.keys():
            defaultVal = self.settings.getDefault(name)
            nowvals[name] = self.altchanneldict[name].getPotValue()
            self.altchanneldict[name].setValue(defaultVal)
            self.altchanneldict[name].setModeChangeValue(nowvals[name])

    def setInputLevel(self, scalar):
        tick = scalar
        prev_ticks = self.in_ticks
        self.in_ticks = tick
        if prev_ticks != self.in_ticks:
            cmd = 'amixer set \'Capture\' ' + str(tick)
            os.system(cmd)

    def getEndOfLoopState(self):
        return self.eol_state

    def handleEndOfLoop(self):
        self.eol_comm.update()
        self.size_status_comm.update()
        if self.size_status_comm.getState() == 0:
            if self.eol_comm.getState() > 0:
                GPIO.output(self.eol_pin, False)
            else:
                GPIO.output(self.eol_pin, True)
        #    if self.eol_comm.getState() == 1:
        #        self.eol_comm.clearState()
        #        GPIO.output(self.eol_pin, False)
        #        self.eol_gate_timer = 0
        #        self.eol_state = True
        #    if self.eol_state is True:
        #        self.eol_gate_timer += 1
        #        if self.eol_gate_timer > 2:
        #           GPIO.output(self.eol_pin, True) 
        #           self.eol_state = False
        else:
            GPIO.output(self.eol_pin, True)

    # Listens for changes in the actual recording state of CSound
    def handleRecordStatus(self):
        self.record_status_comm.update()
        if self.record_status_comm.fallingEdge() == True:
            print "Ending recording."
            if self.getAltValue("record_alt") == 0:
                self.setValue("record", 0)
                if self.getValue("source") == 1:
                    self.setValue("pitch", 0.6)
                    self.setValue("speed", 0.625)
        

    def getEditFunctionFlag(self, name):
        if self.editFunctionFlag.has_key(name):
            return self.editFunctionFlag[name]
        else:
            return False

    def clearEditFunctionFlag(self,name):
        if self.editFunctionFlag.has_key(name):
            self.editFunctionFlag[name] = False

    def setEditFunctionFlag(self,name):
        if self.editFunctionFlag.has_key(name):
            self.editFunctionFlag[name] = True

    def updateAll(self): 
        #GPIO.output(self.eol_pin, False) # For debugging
        numChanged = 0
        self.now = int(round(time.time() * 1000))
        self.shiftReg.update()
        self.sourceStateCtrl.update()
        #print "source state: " + str(self.sourceStateCtrl.getValue())
        if self.sourceStateCtrl.getValue() == 1 and self.sourceStateCtrl.getPrevValue() == 0: 
            self.prep_mode_change = True
            self.prep_mode_change_time = self.now
            #for chn in self.channeldict:
        elif self.sourceStateCtrl.getValue() == 0: 
            for chn in self.channels:
                self.modeChangeValues[chn.name] = chn.getValue()
            if self.sourceStateCtrl.getPrevValue() == 1:
                self.prep_mode_change = False
                if self.control_mode == "secondary controls":
                    if self.prev_control_mode == "puredata":
                        self.enterPureDataMode()
                    else:
                        self.enterNormalMode()
        if self.prep_mode_change == True and self.now - self.prep_mode_change_time > 175:# and numChanged > 0:
            self.enterSecondaryMode()
            self.prep_mode_change = False
            self.channeldict["source"].setIgnoreNextButton()
            #self.altchanneldict["source_alt"].setIgnoreNextButton()
        if self.control_mode != "puredata":
            self.handleEndOfLoop()
            self.handleRecordStatus()
        #self.printAllControls()
        if self.control_mode == "secondary controls":
            if self.prev_control_mode == "puredata":          
                time.sleep(0.001)
                msgs = []
                for chn in self.channels:
                    #chn.setIgnoreHID(False)
                    chn.update()
                    temp_str = chn.name + ' ' + str(chn.getValue())
                    msgs.append(temp_str)
                for chn in self.altchannels:
                    chn.update()
                    temp_str = chn.name + ' ' + str(chn.getValue())
                    msgs.append(temp_str)
                try:
                    self.pdSock.send(msgs)
                except:
                    if self.pdSock.is_connected():
                        print 'Could not send messages to PD. Connected, but error?'
                    else:
                        print 'Could not send messgaes to PD. No connection?'
            else:
                for chn in self.channels:
                    chn.update()
                for chn in self.altchannels:
                    chn.update()
                    self.settings.save(chn.name, chn.getValue())
                if self.currentInstr == "a_granularlooper":
                    self.channeldict["file"].input.setIncOrder(self.altchanneldict["file_alt"].getValue()) 
            in_scalar = self.altchanneldict["speed_alt"].getValue()
            self.setInputLevel(in_scalar)
            #if self.altchanneldict["reset_alt"].curVal == True and self.altchanneldict["reset_alt"].prevVal == False:
                #print "Storing Current Settings"
                #self.settings.update(self.now)
                #self.settings.write()
                #self.setEditFunctionFlag("reset")
            #    print "Restoring Defaults!"
            #    if self.control_mode == "secondary controls":
            #        self.restoreAltToDefault()
        elif self.control_mode == "instr selector":
            #self.exit_instrmode_chn.update()
            for idx, chn in enumerate(self.instr_sel_controls):
                chn.update()
                if chn.getValue() == 1:
                    sel_idx = idx + self.instr_sel_offset
                    if sel_idx < self.instr_sel_numfiles:
                        self.instr_sel_idx = sel_idx
                
        elif self.control_mode == "puredata":
            time.sleep(0.001)
            msgs = []
            for chn in self.channels:
                if chn.name != "sourcegate":
                    chn.setIgnoreHID(False)
                chn.update()
                temp_str = chn.name + ' ' + str(chn.getValue())
                msgs.append(temp_str)
            try:
                self.pdSock.send(msgs)
            except:
                if self.pdSock.is_connected():
                    print 'Could not send messages to PD. Connected, but error?'
                else:
                    print 'Could not send messgaes to PD. No connection?'
        else: #includes "normal":4
            filestate = self.channeldict["filestate"].getValue()
            source_state = self.getValue("source")
            if self.getAltValue("freeze_alt") == 1 and self.currentInstr == "a_granularlooper":
                self.channeldict["source"].setIgnoreGate(True)
            else:
                self.channeldict["source"].setIgnoreGate(False)
                        
            for chn in self.channels:
                if chn.name != "sourcegate":
                    chn.setIgnoreHID(False)
                chn.update()
                #if abs(chn.getValue() - chn.getPrevValue()) > 0.005 and chn.name != "source":
                if self.modeChangeValues.has_key(chn.name):
                    if abs(chn.getValue() - self.modeChangeValues[chn.name]) > 0.005:
                        numChanged += 1
                ## UNIQUE INSTR HANDLING
                if self.currentInstr == "a_granularlooper":
                    if chn.name == "file":
                        if source_state == 1:
                            chn.setValue(self.static_file_idx)
                        else:
                            self.static_file_idx = self.getValue("file")
                if chn.name != "filestate":
                    if chn.source == "hybrid":
                        self.settings.save(chn.name, chn.getStaticVal())
                    else:
                        self.settings.save(chn.name, chn.getValue())
                    if chn.source == "digital" and chn.name != "file": 
                        if filestate == 1 or filestate == True:
                            if chn.hasChanged() == True and chn.getTrigSource() == "button":
                                if chn.name == "reset":
                                    self.setEditFunctionFlag(chn.name)
                                elif chn.name == "source":
                                    self.setEditFunctionFlag(chn.name) 
                                    self.channeldict[chn.name].setIgnoreNextButton()
                                elif chn.name == "freeze":
                                    self.setEditFunctionFlag(chn.name) 
                                    self.channeldict[chn.name].setIgnoreNextButton()
                                    self.channeldict[chn.name].setValue(1 - self.channeldict[chn.name].getValue())
                                    #self.writeBufferToAudioFile()
                                    if self.writeThread.isAlive() == False:
                                        print("Write Thread Starting!")
                                        self.writeThread.join()
                                        self.writeThread = threading.Thread(target=self.writeBufferToAudioFile)
                                        self.writeThread.start()
                                        #self.writeThread.start()
                                    else:
                                        print("Write thread still running.")
                                print "channel: " + chn.name + " has changed."
                                self.channeldict["file"].setIgnoreNextButton()
        #GPIO.output(self.eol_pin, True) # for debugging

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
        line += "\nComm Channels:"
        line += "krecordstatus: " + str(self.record_status_comm.getState()) + '\n'
        line += "\n############################\n"
        print line

    def printAllControlsVerbose(self):
        line = "############################\n"
        line += "Primary Channel Pots:"
        for i,chn in enumerate(self.channels):
            if i % 4 == 0:
                line +="\n"
            line += chn.name + ": " + str(chn.getPotValue()) + "\t"
        line += "\nPrimary Channel CVs:"
        for i,chn in enumerate(self.channels):
            if i % 4 == 0:
                line +="\n"
            line += chn.name + ": " + str(chn.getCVValue()) + "\t"
        line += "\nSecondary Channels:"
        for i,chn in enumerate(self.altchannels):
            if i % 4 == 0:
                line += "\n"
            line += chn.name + ": " + str(chn.getValue()) + "\t"
        line += "\n############################\n"
        print line

    def writeBufferToAudioFile(self):
        # Get Tables from csound
        success = False
        silence_audio = False
        if self.csound is not None:
            print("Started Writing Buffer")
            self.writing_buffer = True
            self.buffer_size_comm.update()
            length = self.buffer_size_comm.getState()
            if (length > 0):
                print length
                if self.performance_thread is not None and silence_audio is True:
                    self.performance_thread.pause()
                print("Getting tables from Csound")
                dataLeft = self.csound.table(200)
                dataRight = self.csound.table(201)
                print("Jumping to WaveWriter")
                # Format down to 16-bit signed
                success = self.writer.WriteStereoWaveFile(dataLeft, dataRight, length)
                if self.performance_thread is not None and silence_audio is True:
                    self.performance_thread.play()
                print("Finished Writing Buffer")
            else:
                print("Buffer is currently empty")
            self.writing_buffer = False
        if success == False:
            self.buffer_failure = True

    def dummyThread(self):
        print "This is a dummy function for initializing a worker thread."
