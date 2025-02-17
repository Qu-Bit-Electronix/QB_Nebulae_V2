import Adafruit_GPIO.SPI as SPI
import RPi.GPIO as GPIO
import MCP3208
import ctcsound
import switch as libSwitch
import shiftregister as libSR
import random
import os
import digitaldata
import time
# Hardware SPI configuration:
SPI_PORT   = 0
SPI_DEVICE_CV = 0
SPI_DEVICE_POT = 1

POT_Sel_Pin = 7
CV_Sel_Pin = 8
EOL_OUT_PIN = 16

# Defines for Button/Gate Types
BUTTON_GATE_GPIO = 0
BUTTON_SR_GATE_GPIO = 1
BUTTON_GATE_SR = 2
BUTTON_GPIO_GATE_SR = 3
BUTTON_GPIO_GATE_NONE = 4
BUTTON_SR_GATE_NONE = 5

def addHysteresis(cur, new, distance):
    output = cur
    if cur + distance < new:
        output = new
    elif cur - distance > new:
        output = new
    return output

def averageInput(new_val, hist, hist_size, hist_idx):
    if len(hist) > hist_size - 1:
        old_val = hist.pop()
    hist.insert(0,new_val)
    temp_avg = 0
    for val in hist:
        temp_avg += val
    temp_avg /= hist_size
    return temp_avg

# Class for handling ADC Input Data
class AdcData(object):
    def __init__(self, pot_channel, cv_channel, minimum, maximum, init_val=0.0):
        self.minimum = minimum
        self.maximum = maximum
        self.range = maximum - minimum
        self.curVal = minimum
        self.cv_offset = 0.011
        self.pot_channel = pot_channel
        self.cv_channel = cv_channel
        self.hist = []
        self.hist_size = 8
        self.hist_idx = 0
        self.average = 0.0
        self.raw_pot = init_val
        self.raw_cv = init_val
        self.static_pot = init_val
        self.resist_val = 0
        self.resisting_change = False
        self.ignoring_pot = False
        self.curminpot = self.raw_pot / 4095
        self.curmaxpot = self.raw_pot / 4095
        self.curmincv = 2048
        self.curmaxcv = 2048
        self.count = 0
        self.filtPotVal = 0
        self.filtCVVal = 0
        #self.smoothCoeff = 0.125
        self.smoothCoeff = 0.33
        self.hyst_amt = 0.002
        self.stablized = True
        self.stable_delta = 0.0
        self.last_in = 0.0
        if (pot_channel >= 0):
            self.mcp_pot = MCP3208.MCP3208(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE_POT))
        if (cv_channel >= 0):
            self.mcp_cv = MCP3208.MCP3208(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE_CV))

    def setIgnoreHID(self, state):
        self.ignoring_pot = state

    def convertRawCV(self, cv_in):
        return ((4095 - cv_in) - 2047) / 2047.0

    def setResistVal(self, value):
        self.resisting_change = True
        self.resist_val = value

    def clearResistVal(self):
        self.resisting_change = False

    def isResisting(self):
        return self.resisting_change

    def getRawPotValue(self):
        return self.raw_pot

    def getRawCVValue(self):
        return self.raw_cv

    def getPotValue(self):
        return self.filtPotVal

    def getCVValue(self):
        return self.raw_cv - self.cv_offset

    def getValue(self):
        cv = self.getCV()
        pot = self.getPot()
        temp_sum = cv + pot
        temp_rnd = round(temp_sum, 4)
        temp_hyst = addHysteresis(self.curVal, temp_rnd, self.hyst_amt)
        if self.stablized is True:
            if abs(temp_hyst - self.curVal) > 0.01:
                self.stablized = False
        else:
            #self.stable_delta += abs(temp_hyst - self.curVal)
            #self.stable_delta += 0.001 * (abs(temp_hyst - self.curVal) - self.stable_delta)
            if abs(self.stable_delta) < 0.005:
                self.stablized = True
            else:
                self.curVal = self.clipControl(temp_hyst)
        self.stable_delta = (temp_rnd - self.last_in) + (0.99 * self.stable_delta)
        self.last_in = temp_rnd
        return self.curVal


    # TODO: Implement this so that it handles the analog alternate controls.
    # In retrospect having two completely independent objects for primary/secondary is a nightmare.
    def getAltValue(self):
        if self.resisting_change == True:
            pot = self.filtPotVal
            temp_rnd = round(pot, 4)
            temp_hyst = addHysteresis(self.curAltVal, temp_rnd, self.hyst_amt)
            self.curAltVal =  self.clipControl(temp_hyst)
            return self.curAltVal

    def getCV(self):
        if (self.cv_channel >= 0):
            #temp_cv_code = (self.mcp_cv.read_adc(self.cv_channel)) / 8
            #temp_cv = ((511.0 - temp_cv_code) - 255.0) / 255.0
            temp_cv_code = self.mcp_cv.read_adc(self.cv_channel)
            temp_cv = ((4095.0 - temp_cv_code) - 2047.0) / 2047.0
            self.raw_cv = temp_cv
            temp_cv -= self.cv_offset
        else:
            temp_cv = 0.0
        self.filtCVVal += self.smoothCoeff * (temp_cv - self.filtCVVal)
        return self.filtCVVal

    def getPot(self):
        if self.pot_channel >= 0:
            temp_pot_code = self.mcp_pot.read_adc(self.pot_channel)
            temp_pot = (temp_pot_code >> 3) / 511.0
            self.raw_pot = temp_pot
            self.filtPotVal += self.smoothCoeff * (temp_pot - self.filtPotVal)
            if self.resisting_change is True:
                temp_hyst = addHysteresis(self.resist_val, self.raw_pot, 0.1)
                if temp_hyst != self.resist_val:
                    self.resisting_change = False
                    self.resist_val = self.raw_pot
                pot = self.static_pot
            else:
                if self.ignoring_pot == False:
                    pot = self.filtPotVal
                    self.static_pot = pot
                else:
                    pot = self.static_pot
        else:
            pot = 0.0
        return pot


    def clipControl(self, val):
        if val < self.minimum + (self.hyst_amt * 4):
            val = self.minimum
        if val > self.maximum - (self.hyst_amt * 4):
            val = self.maximum
        return val

    def setCVOffset(self, value):
        self.cv_offset = value

    def setValue(self, val):
        self.static_pot = val
        self.setResistVal(val)

    def evaluateNoise(self):
        self.count += 1
        if self.count > 100:
            self.count = 0
            self.curminpot = temp_pot_code
            self.curmaxpot = temp_pot_code
            self.curmincv = temp_cv_code
            self.curmaxcv = temp_cv_code
        if temp_pot_code > self.curmaxpot:
            self.curmaxpot = temp_pot_code
        if temp_pot_code < self.curminpot:
            self.curminpot = temp_pot_code
        if temp_cv_code > self.curmaxcv:
            self.curmaxcv = temp_cv_code
        if temp_cv_code < self.curmincv:
            self.curmincv = temp_cv_code
        print "########### SIGS ########"
        print "POT: Current Code: " + str(temp_pot_code) + " Translated Value: " + str(self.raw_pot) + " min: " + str(self.curminpot) + " max: " + str(self.curmaxpot) + " range: " + str(self.curmaxpot - self.curminpot) + " channel " + str(self.pot_channel)
        print "CV:  Current Code: " + str(temp_cv_code) + " Translated Value: " + str(temp_cv) + " min: " + str(self.curmincv) + " max: " + str(self.curmaxcv) + " range: " + str(self.curmaxcv - self.curmincv) + " channel " + str(self.cv_channel)


class StaticData(object):
    def __init__(self, init_val):
        self.curVal = init_val

    def getValue(self):
        return self.curVal

    def setValue(self, value):
        self.curVal = value

class HybridData(object):
    def __init__(self, channel, name, minimum, maximum, init_val):
        self.init  = init_val
        self.curVal = init_val
        self.curMin = init_val
        self.curMax = init_val
        self.name = name
        self.hystVal = init_val
        if self.name == "pitch":
            self.minimum = -0.30
            self.maximum = 1.30
            #self.offset = 0.038
            #self.offset = 0.03225 # Rev 9 pre cap
            #self.scaling = 0.8818342152 # Rev 9 pre cap
            self.offset = 0.0270 # Rev 9 post cap
            #self.scaling = 0.8768342152 # Rev 9 post cap
            #self.scaling = 0.8745 # Rev10 with my seq...
            self.scaling = 0.8685 # Rev13
            ## TODO recalibrate for rev10
            #self.filtCoeff = 0.20
            self.filtCoeff = 0.33
        else:
            self.minimum = minimum
            self.maximum = maximum
            self.scaling = 1.0
            self.offset = -0.0049
            self.filtCoeff = 0.43
        self.range = self.maximum - self.minimum
        self.channel = channel
        if (channel >= 0):
            self.mcp_cv = MCP3208.MCP3208(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE_CV))
            self.mcp_pot = MCP3208.MCP3208(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE_POT))
        self.average = 0.0
        self.analogVal = 0.0
        self.filtVal = 0.0
        self.count = 0
        self.raw_cv = 0
        self.stable_delta = 0.0
        self.stablized = True
        self.last_in = 0.0
        self.staticVal = init_val
        self.ignore_enc = False
        self.new_calibration = False

    def getValue(self):
        #hyst_amt = 0.0025
        hyst_amt = 0.001
        if (self.channel >= 0):
            temp_code = self.mcp_cv.read_adc(self.channel)
            temp_analog = ((1.0 - (temp_code / 4095.0)) * self.range) + self.minimum
            #temp_code = self.mcp_cv.read_adc(self.channel) >> 3
            #temp_analog = ((1.0 - (temp_code / 511.0)) * self.range) + self.minimum
            # temp_analog *= self.scaling # Moved scaling to the output
            self.raw_cv = temp_analog
        else:
            temp_analog = 0.0
            self.filtVal = 0.0
        if self.name is "speed":
            temp_analog = (temp_analog * 2.0) - 1.0
            self.raw_cv = temp_analog
        if (self.channel >= 0):
            temp_rnd = temp_analog * self.scaling
            self.filtVal += self.filtCoeff * (temp_rnd - self.filtVal)
            # Apply scale and offset from calibration..
            if self.name == "pitch" and self.new_calibration:
                self.analogVal = self.offset + self.filtVal
            else:
                self.analogVal = self.filtVal - self.offset
            self.hystVal = addHysteresis(self.hystVal, self.analogVal, hyst_amt)
            temp = self.hystVal + self.staticVal
            temp_rnd = round(temp, 4)
            if self.name == "speed":
                tolerance = 0.00208 # 1/8 semi-tone = quarter tone tolerance.
                factors = [0.0, 0.125, 0.25, 0.5, 1.0, 2.0, 4.0]
                for f in factors:
                    factor_val_pos = (f + 4.0) / 8.0
                    factor_val_neg = ((-1.0 * f) + 4.0) / 8.0
                    if temp_rnd < factor_val_pos + tolerance and temp_rnd > factor_val_pos - tolerance:
                        temp_rnd = factor_val_pos
                    if temp_rnd < factor_val_neg + tolerance and temp_rnd > factor_val_neg - tolerance:
                        temp_rnd = factor_val_neg
            elif self.name == "pitch":
                tolerance = 0.00208
                octaves = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
                for octave in octaves:
                    if temp_rnd < octave + tolerance and temp_rnd > octave - tolerance:
                        temp_rnd = octave
            if self.stablized is True:
                if abs(temp_rnd - self.curVal) > 0.005:
                    self.stablized = False
            else:
                if abs(self.stable_delta) < 0.005:
                    self.stablized = True
                self.curVal = temp_rnd
            # Leaky Integrator for checking stablity
            self.stable_delta = (temp_rnd - self.last_in) + (0.99 * self.stable_delta)
            self.last_in = temp_rnd
        else:
            self.curVal = self.staticVal
        if (self.curVal > self.maximum):
            self.curVal = self.maximum
        elif (self.curVal < self.minimum):
            self.curVal = self.minimum
        #self.count += 1
        #if self.count > 150:
        #    self.count = 0
        #    self.curMax = temp_code
        #    self.curMin = temp_code
        #if temp_code > self.curMax:
        #    self.curMax = temp_code
        #if self.curVal < self.curMin:
        #    self.curMin = temp_code
        #noise_range = self.curMax - self.curMin
        #if self.name == "speed":
        #    print "###### SPEEED #######"
        #    print "Val: " + str(self.curVal) + " CV: " + str(self.filtVal) +  " CV Code: " + str(temp_code) + " Scaling: " + str(self.scaling)
        #    print "Cur Max: " + str(self.curMax) + " Cur Min: " + str(self.curMin) + " Noise Range: " + str(noise_range) + " dummy code: " + str(temp_dummy_code) + " diff: " + str(temp_code)
        return self.curVal

    def setCVOffset(self, value):
        self.offset = value

    def setCVScaling(self, value):
        """
        This is only used with the new calibration added for pitch/voct

        So, this will _also_ tell the class to use the new calibration scheme
        which handles its offset in the opposite direction.
        """
        self.new_calibration = True
        self.scaling = value

    def setIgnoreHID(self, state):
        self.ignore_enc = state

    def setValue(self, value):
        if self.ignore_enc is False:
            self.staticVal = value

    def getStaticVal(self):
        return self.staticVal

    def getRawCVValue(self):
        return self.raw_cv

    def getCVValue(self):
        ## Note to future self: this does not get used anywhere...
        return (self.raw_cv * self.scaling) - self.offset





# Single Channel of Return Communication from CSound
class CommChannel(object):
    def __init__(self, csound, name):
        self.prev_state = 0
        self.state = 0
        self.rising_edge_flag = False
        self.csound = csound
        self.name = name
        if self.csound is not None:
            chn, _ = self.csound.channelPtr(self.name,
                ctcsound.CSOUND_CONTROL_CHANNEL | ctcsound.CSOUND_OUTPUT_CHANNEL)
            self.channel = chn
        else:
            self.channel = None

    def update(self):
        if self.channel is not None:
            temp = self.csound.controlChannel(self.name)
            self.prev_state = self.state
            self.state = temp[0]
            if self.state > 0.0 and self.prev_state < 1.0:
                self.rising_edge_flag = True
            else:
                self.rising_edge_flag = False

    def getState(self):
        return self.state

    def risingEdge(self):
        if self.state == 1 and self.prev_state == 0:
            return True
        else:
            return False

    def fallingEdge(self):
        if self.state == 0 and self.prev_state == 1:
            return True
        else:
            return False

    def clearState(self):
        if self.channel is not None:
            if self.state == 1:
                self.state = 0
                self.csound.setControlChannel(self.name, self.state)


# Single Channel of Control Information
class ControlChannel(object):
    def __init__(self, csound, name, init = 0, source="static", data_channel=-1, sr=None, gate_pin=-1, button_pin=-1, config=None, minimum=0, maximum=1, cvchn=-2, longtouch_cb=None):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(CV_Sel_Pin, GPIO.OUT)
        GPIO.setup(POT_Sel_Pin, GPIO.OUT)
        GPIO.setup(EOL_OUT_PIN, GPIO.OUT)
        GPIO.output(CV_Sel_Pin, True)
        GPIO.output(POT_Sel_Pin, True)
        self.csound = csound
        self.name = name
        if self.csound is not None:
            chn, _ = self.csound.channelPtr(self.name,
                ctcsound.CSOUND_CONTROL_CHANNEL | ctcsound.CSOUND_INPUT_CHANNEL)
            self.channel = chn
        else:
            self.channel = [0, 0] # Just a dummy list so csound doesn't need to be here.
        self.curVal = init
        self.prevVal = init
        self.mute_csound = False
        self.channel[0] = self.curVal
        self.source = source
        self.sr = sr

        if config is not None:
            mode = config[0]
            edge = config[1]
        else:
            mode = "latching"
            edge = "falling"

        if (cvchn is -2):
            cvchn = data_channel
        if (self.source is "analog"):
            self.input = AdcData(data_channel, cvchn, minimum, maximum, init_val=init)
        elif (source is "static"):
            self.input = StaticData(self.curVal)
        elif (source is "digital"):
            if self.sr is not None:
                self.input = digitaldata.DigitalData(self.name, data_channel, gate_pin, button_pin, self.sr, mode, edge, maximum, longtouch_cb, init_val=init)
        elif (source is "hybrid"):
            self.input = HybridData(data_channel, self.name, minimum, maximum, init_val=self.curVal)

        if self.source == "analog" or self.source == "hybrid":
            new_offset = self.gatherOffset(self.name)
            #print name + ": new offset = " + str(new_offset)
            self.setCVOffset(new_offset)

        # Use new 1V/oct calibration if available
        has_voct_cal = self.hasOffset("pitch_voct_offset") and self.hasOffset("pitch_voct_scale")
        if self.name == "pitch" and has_voct_cal:
            voct_offset = self.gatherOffset("pitch_voct_offset")
            voct_scale = self.gatherOffset("pitch_voct_scale")
            self.setCVOffset(voct_offset)
            self.setCVScaling(voct_scale)

    def setValue(self, val):
        self.input.setValue(val)
        self.curVal = self.input.getValue()
        if self.mute_csound == False:
            self.channel[0] = self.curVal

    def getValue(self):
        return self.curVal

    def getPrevValue(self):
        return self.prevVal

    def getPotValue(self):
        if self.source == "analog":
            val = self.input.getPotValue()
            return val

    def getRawCVValue(self):
        if self.source == "analog" or self.source == "hybrid":
            val = self.input.getRawCVValue()
            return val

    def getCVValue(self):
        if self.source == "analog" or self.source == "hybrid":
            val = self.input.getCVValue()
            return val

    def getStaticVal(self):
        if self.source == "hybrid":
            val = self.input.getStaticVal()
            return val

    def setCVOffset(self, value):
        if self.source == "hybrid" or self.source == "analog":
            self.input.setCVOffset(value)

    def setCVScaling(self, value):
        if self.source == "hybrid":
            self.input.setCVScaling(value)

    def setIgnoreNextButton(self):
        if self.source == "digital":
            self.input.setIgnoreNextButton()

    def setModeChangeValue(self, value_to_resist):
        if self.source == "analog":
            self.input.setResistVal(value_to_resist)

    def clearResistVal(self):
        if self.source == "analog":
            self.input.clearResistVal()

    def isResisting(self):
        if self.source == "analog":
            return self.input.isResisting()
        else:
            return False

    def hasChanged(self):
        change = self.curVal != self.prevVal
        return change

    def setIgnoreHID(self, state):
        if self.source == "analog" or self.source == "digital" or self.source == "hybrid":
            self.input.setIgnoreHID(state)

    def setIgnoreGate(self, state):
        if self.source == "digital":
            self.input.setIgnoreGate(state)

    def getTrigSource(self):
        if self.source == "digital":
            ret = self.input.getTrigSource()
        else:
            ret = "none"
        return ret

    def muteCSound(self, state):
        self.mute_csound = state

    def isCSoundMuted(self):
        return self.mute_csound

    def getLEDValue(self):
        if self.source == "digital":
            return self.input.getLEDValue()
        else:
            return self.curVal

    def hasOffset(self, name):
        filepath = '/home/alarm/QB_Nebulae_V2/Code/misc/'
        filename = 'calibration_data.txt'
        found = False
        try:
            with open(filepath + filename, 'r') as myfile:
                for line in myfile:
                    if line.startswith(name):
                        found = True
                        datalist = line.split(',')
                        try:
                            val = float(datalist[1])
                        except:
                            found = False
                            print 'list value is not a floating point number:' + datalist[1]
        except:
            print 'No file: ' + filepath + filename
        return found


    def gatherOffset(self, name):
        filepath = '/home/alarm/QB_Nebulae_V2/Code/misc/'
        filename = 'calibration_data.txt'
        val = 0.0
        try:
            with open(filepath + filename, 'r') as myfile:
                for line in myfile:
                    if line.startswith(name):
                        datalist = line.split(',')
                        try:
                            val = float(datalist[1])
                        except:
                            print 'list value is not a floating point number:' + datalist[1]
        except:
            print 'No file: ' + filepath + filename
        return val

    def update(self):
        #time.sleep(0.001)
        val = self.input.getValue()
        #if self.name == "reset":
        #    print str(val)
        self.prevVal = self.curVal
        self.curVal = val
        if self.mute_csound == False:
            self.channel[0] = self.curVal
