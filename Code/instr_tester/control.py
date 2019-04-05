#import Adafruit_GPIO.SPI as SPI
#import RPi.GPIO as GPIO
#import MCP3208
import ctcsound
#import switch as libSwitch
#import shiftregister as libSR
import random
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
        self.pot_channel = pot_channel
        self.cv_channel = cv_channel
        self.hist = []
        self.hist_size = 8
        self.hist_idx = 0
        self.average = 0.0
        self.raw_pot = init_val
        self.resist_val = 0
        self.resisting_change = False
        self.ignoring_pot = False
        self.just_set_manually = False
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

    def getPotValue(self):
        return self.raw_pot

    def getValue(self):
        if self.just_set_manually is True:
            self.just_set_manually = False
            self.raw_pot = self.curVal
            self.setResistVal(self.curVal)
            return self.curVal
        if (self.pot_channel >= 0):
            temp_cv = 0.0
            temp_pot = 0.0
            if self.resisting_change is True:
                temp_hyst = addHysteresis(self.resist_val, temp_pot, 0.05) 
                if temp_hyst != self.resist_val:
                    self.resisting_change = False
                temp_sum = (self.raw_pot + temp_cv)
            else:
                if self.ignoring_pot == False:
                    self.raw_pot = temp_pot
                temp_sum = self.raw_pot + temp_cv
            if temp_sum > self.maximum:
                temp_sum = self.maximum
            if temp_sum < self.minimum:
                temp_sum = self.minimum
            temp_avg = averageInput(temp_sum, self.hist, self.hist_size, self.hist_idx)
            temp_rnd = round(((temp_avg * self.range) + self.minimum), 4)
            self.curVal = addHysteresis(self.curVal, temp_rnd, 0.002)
        return self.curVal

    def setValue(self, val):
        self.just_set_manually = True
        self.curVal = val;


class StaticData(object):
    def __init__(self, init_val):
        self.curVal = init_val

    def getValue(self):
        return self.curVal

    def setValue(self, value):
        self.curVal = value

class HybridData(object):
    def __init__(self, channel, name, minimum, maximum):
        self.minimum = minimum
        self.maximum = maximum
        self.range = maximum - minimum
        self.curVal = minimum
        self.name = name
        self.channel = channel
        if (channel >= 0):
            self.mcp_cv = MCP3208.MCP3208(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE_CV))
        self.average = 0.0
        self.analogVal = minimum
        self.staticVal = minimum
        self.ignore_enc = False

    def getValue(self):
        if (self.channel >= 0):
            temp_analog = ((1.0 - (self.mcp_cv.read_adc(self.channel) / 4095.0)) * self.range) + self.minimum
        else:
            temp_analog = 0.0
        if self.name is "speed":
            temp_analog = (temp_analog * 2.0) - 1.0
        if (self.channel >= 0):
            temp_rnd = round(temp_analog, 5)
            self.analogVal = addHysteresis(self.analogVal, temp_rnd, 0.002) # static control sig
            self.curVal = self.analogVal + self.staticVal
        else:
            self.curVal = self.staticVal
        if (self.curVal > self.maximum):
            self.curVal = self.maximum
        elif (self.curVal < self.minimum):
            self.curVal = self.minimum
        return self.curVal 
    
    def setIgnoreHID(self, state):
        self.ignore_enc = state

    def setValue(self, value):
        if self.ignore_enc is False:
            self.staticVal = value

    def getStaticVal(self):
        return self.staticVal

        

class DigitalData(object):
    def __init__(self, name, button_gate_mode, gate_pin, button_pin, sr, mode="latching", edge="falling", maximum=1, longtouch_cb=None, inc_order=0):
        self.g_state = False
        self.b_state = False
        self.gate_pin = gate_pin
        self.button_pin = button_pin
        self.sr = sr
        self.state = 0
        self.edge = edge
        self.mode = mode
        self.maximum = maximum
        self.time_held = 0
        self.button_pressed = False
        self.long_press_time = 300
        #self.long_press_time = 63
        self.ignore_next_btrig = False
        self.name = name
        self.longtouch_cb = longtouch_cb
        self.inc_order = inc_order
        self.ignore_button = False
        self.ignore_gate = False

        if button_gate_mode is BUTTON_GATE_GPIO:
            # Setup both inputs as
            self.gate_src = "GPIO"
            self.button_src = "GPIO"
            self.gate_switch = libSwitch.Switch(gate_pin)
            self.button_switch = libSwitch.Switch(button_pin)
        elif button_gate_mode is BUTTON_SR_GATE_GPIO:
            # Setup button as SR input, and gate as GPIO (most common)
            self.gate_src = "GPIO"
            self.button_src = "SR"
            self.gate_switch = libSwitch.Switch(gate_pin)
            self.button_switch = self.sr
        elif button_gate_mode is BUTTON_GPIO_GATE_SR:
            # Setup Button as GPIO and Gate as SR (doesn't happen)
            self.gate_src = "SR"
            self.button_src = "GPIO"
            self.gate_switch = self.sr
            self.button_switch = libSwitch.Switch(button_pin)
        elif button_gate_mode is BUTTON_GATE_SR:
            # Setup both inputs as SR (source only I believe)
            self.gate_src = "SR"
            self.button_src = "SR"
            self.gate_switch = self.sr
            self.button_switch = self.sr
        elif button_gate_mode is BUTTON_GPIO_GATE_NONE:
            self.gate_src = "NONE"
            self.button_src = "GPIO"
            self.button_switch = libSwitch.Switch(button_pin)
        elif button_gate_mode is BUTTON_SR_GATE_NONE:
            self.gate_src = "NONE"
            self.button_src = "SR"
            self.button_switch = self.sr

    def setIgnoreHID(self, state):
        self.ignore_button = state

    def setIgnoreGate(self, state):
        self.ignore_gate = state

    def setValue(self, val):
        self.state = val

    def setIncOrder(self, val):
        self.inc_order = val

    def setIgnoreNextButton(self):
        self.ignore_next_btrig = True

    def getValue(self):
        if self.mode == "latching":
            if self.gate_src is "GPIO":
                self.gate_switch.update()
                g_trig = self.gate_switch.risingEdge()
            elif self.gate_src is "SR":
                g_trig = self.gate_switch.risingEdge(self.gate_pin)

            if self.ignore_button == False:
                if self.button_src is "GPIO":
                    self.button_switch.update()
                    b_trig = self.button_switch.fallingEdge()
                else:
                    if self.edge == "falling":
                        b_action = self.button_switch.fallingEdge(self.button_pin)
                        if self.button_switch.risingEdge(self.button_pin) is True:
                            self.button_pressed = True
                            self.time_held = 0
                        if self.button_pressed is True:
                            self.time_held += 1
                    else:
                        b_action = self.button_switch.risingEdge(self.button_pin)
                    b_trig = b_action

            # Messing around here
            #if b_trig is True and self.time_held > self.long_press_time and self.edge is "falling":
                if self.time_held > self.long_press_time and self.edge == "falling":
                    b_trig = False
                    self.ignore_next_btrig = True
                    self.button_pressed = False
                    self.time_held = 0
                    print "You long pressed a button!"
                    if self.longtouch_cb is not None:
                        self.longtouch_cb()

                if self.ignore_next_btrig is True:
                    if b_trig is True:
                        b_trig = False
                        self.ignore_next_btrig = False

            if self.ignore_gate is True or  "_alt" in self.name:
                g_trig = False
            
            if self.ignore_button is True:
                b_trig = False

            if g_trig is True or b_trig is True:
                if b_trig is True:
                    self.button_pressed = False
                    self.time_held = 0
                if self.state is 0:
                    self.state = 1 
                else:
                    self.state = 0
            
        elif self.mode == "triggered":
            if self.gate_src is "GPIO":
                self.gate_switch.update()
                g_trig = self.gate_switch.state()
            elif self.gate_src is "SR":
                g_trig = not self.gate_switch.state(self.gate_pin)
            else:
                g_trig = False

            if self.ignore_button == False:
                if self.button_src is "GPIO":
                    self.button_switch.update()
                    if self.edge == "rising":
                        b_trig = self.button_switch.state()
                    else: 
                        b_trig = self.button_switch.fallingEdge()
                        if self.button_switch.risingEdge() is True:
                            self.button_pressed = True
                            self.time_held = 0
                        if self.button_pressed is True:
                            self.time_held += 1
                    if self.time_held > self.long_press_time and self.edge == "falling":
                        b_trig = False
                        self.button_pressed = False
                        self.time_held = 0
                        print "You long pressed a button!"
                        if self.longtouch_cb is not None:
                            self.longtouch_cb()
                else:
                    if self.edge == "rising":
                        b_trig = self.button_switch.state(self.button_pin)
                    else:
                        b_trig = self.button_switch.fallingEdge(self.button_pin)
                        if b_trig is True:
                            self.button_pressed = False
                            self.time_held = 0
                        if self.button_switch.risingEdge(self.button_pin) is True:
                            self.button_pressed = True
                            self.time_held = 0
                        if self.button_pressed is True:
                            self.time_held += 1
                    if self.time_held > self.long_press_time and self.edge == "falling":
                        b_trig = False
                        self.button_pressed = False
                        self.time_held = 0
                        print "You long pressed a button!"
                        if self.longtouch_cb is not None:
                            self.longtouch_cb()
                    
            if self.ignore_gate is True or  "_alt" in self.name:
                g_trig = False
            if self.ignore_button is True:
                b_trig = False
            if g_trig is True or b_trig is True:
                self.state = 1
            else:
                self.state = 0

        elif self.mode == "incremental":
            if self.gate_src is "GPIO":
                self.gate_switch.update()
                g_trig = self.gate_switch.risingEdge()
            elif self.gate_src is "SR":
                g_trig = self.gate_switch.risingEdge(self.gate_pin)
            else:
                g_trig = False

            if self.button_src is "GPIO":
                self.button_switch.update()
                if self.edge == "rising":
                    b_trig = self.button_switch.risingEdge()
                else:
                    b_trig = self.button_switch.fallingEdge()
            else:
                if self.edge == "rising":
                    b_trig = self.button_switch.risingEdge(self.button_pin)
                else:
                    b_trig = self.button_switch.fallingEdge(self.button_pin)
            if self.ignore_button == False:
                if self.button_switch.risingEdge(self.button_pin) is True:
                    self.button_pressed = True
                    self.time_held = 0
                if self.button_pressed is True:
                    self.time_held += 1
                if self.time_held > self.long_press_time and self.edge == "falling":
                    b_trig = False
                    self.button_pressed = False
                    self.time_held = 0
                    print "You long pressed a button!"
                    if self.longtouch_cb is not None:
                        self.longtouch_cb()
            if self.ignore_next_btrig is True:
                if b_trig is True:
                    b_trig = False
                    self.ignore_next_btrig = False
            if self.ignore_gate is True or  "_alt" in self.name:
                g_trig = False
            if self.ignore_button is True:
                b_trig = False
            if g_trig is True or b_trig is True:
                if self.inc_order == 0:
                    self.state += 1
                    if self.state >= self.maximum:
                        self.state = 0
                elif self.inc_order == 1:
                    self.state -= 1
                    if self.state < 0:
                        self.state = self.maximum - 1
                elif self.inc_order == 2:
                    self.state = random.randint(0,self.maximum - 1)
                if b_trig is True:
                    self.time_held = 0
                    self.button_pressed = False
        elif self.mode == "momentary":
            if self.gate_src is "GPIO":
                self.gate_switch.update()
                g_trig = self.gate_switch.state()
            elif self.gate_src is "SR":
                g_trig = self.gate_switch.state(self.gate_pin)
            else:
                g_trig = False
            if self.button_src is "GPIO":
                self.button_switch.update()
                if self.edge == "rising":
                    b_trig = self.button_switch.state()
                else:
                    b_trig = self.button_switch.state()
            else:
                if self.edge == "rising":
                    b_trig = self.button_switch.state(self.button_pin)
                else:
                    b_trig = self.button_switch.state(self.button_pin)
            if self.ignore_gate is True:
                g_trig = False
            if self.ignore_button is True:
                b_trig = False
            if g_trig is True or b_trig is True or b_trig is 1:
                self.state = True
            else:
                self.state = False

        return self.state
                

# Single Channel of Return Communication from CSound
class CommChannel(object):
    def __init__(self, csound, name):
        self.prev_state = 0
        self.state = 0
        self.rising_edge_flag = False
        self.csound = csound
        self.name = name
        chn, _ = self.csound.channelPtr(self.name,
            ctcsound.CSOUND_CONTROL_CHANNEL | ctcsound.CSOUND_OUTPUT_CHANNEL)
        self.channel = chn

    def update(self):
        temp = self.csound.controlChannel(self.name)
        self.prev_state = self.state
        self.state = temp[0]
        if self.state > 0.0 and self.prev_state < 1.0:
            self.rising_edge_flag = True
        else:
            self.rising_edge_flag = False

    def getState(self):
        return self.state

    def clearState(self):
        if self.state == 1:
            self.state = 0
            self.csound.setControlChannel(self.name, self.state)
        

# Single Channel of Control Information
class ControlChannel(object):
    def __init__(self, csound, name, init = 0, source="static", data_channel=-1, sr=None, gate_pin=-1, button_pin=-1, config=None, minimum=0, maximum=1, cvchn=-2, longtouch_cb=None):
        #GPIO.setmode(GPIO.BCM)
        #GPIO.setwarnings(False)
        #GPIO.setup(CV_Sel_Pin, GPIO.OUT)
        #GPIO.setup(POT_Sel_Pin, GPIO.OUT)
        #GPIO.setup(EOL_OUT_PIN, GPIO.OUT)
        #GPIO.output(CV_Sel_Pin, True)
        #GPIO.output(POT_Sel_Pin, True)
        self.csound = csound
        self.name = name
        chn, _ = self.csound.channelPtr(self.name, 
            ctcsound.CSOUND_CONTROL_CHANNEL | ctcsound.CSOUND_INPUT_CHANNEL)
        self.channel = chn
        self.curVal = init
        self.prevVal = init
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
                self.input = DigitalData(self.name, data_channel, gate_pin, button_pin, self.sr, mode, edge, maximum, longtouch_cb)
        elif (source is "hybrid"):
            self.input = HybridData(data_channel, self.name, minimum, maximum)

    def setValue(self, val):
        self.input.setValue(val)
        self.curVal = self.input.getValue()
        self.channel[0] = self.curVal

    def getValue(self):
        return self.curVal

    def getPotValue(self):
        if self.source == "analog":
            val = self.input.getPotValue()
            return val

    def getStaticVal(self):
        if self.source == "hybrid":
            val = self.input.getStaticVal()
            return val

    def setIgnoreNextButton(self):
        if self.source == "digital":
            self.input.setIgnoreNextButton()

    def setModeChangeValue(self, value_to_resist):
        if self.source == "analog":
            self.input.setResistVal(value_to_resist)

    def hasChanged(self):
        change = self.curVal != self.prevVal
        return change

    def setIgnoreHID(self, state):
        if self.source == "analog" or self.source == "digital" or self.source == "hybrid":
            self.input.setIgnoreHID(state)

    def setIgnoreGate(self, state):
        if self.source == "digital":
            self.input.setIgnoreGate(state)

    def update(self):
        val = self.input.getValue()
        #if self.name == "reset":
        #    print str(val)
        self.prevVal = self.curVal
        self.curVal = val
        self.channel[0] = self.curVal
