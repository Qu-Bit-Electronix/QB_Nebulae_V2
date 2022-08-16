import switch as libSwitch
import shiftregister as libSR
import time
import random
# Defines for Button/Gate Types
BUTTON_GATE_GPIO = 0
BUTTON_SR_GATE_GPIO = 1
BUTTON_GATE_SR = 2
BUTTON_GPIO_GATE_SR = 3
BUTTON_GPIO_GATE_NONE = 4
BUTTON_SR_GATE_NONE = 5
class DigitalData(object):
    def __init__(self, name, button_gate_mode, gate_pin, button_pin, sr, mode="latching", edge="falling", maximum=1, longtouch_cb=None, inc_order=0, init_val=0):
        self.b_state = 0
        self.g_state = 0
        self.gate_pin = gate_pin
        self.button_pin = button_pin
        self.sr = sr
        self.prev_state = int(init_val)
        self.state = int(init_val)
        self.led_state = int(init_val)
        self.edge = edge
        self.mode = mode
        self.gate_pulse_time = time.time() * 1000.0
        self.button_pulse_time = time.time() * 1000.0
        self.led_pulse_time = time.time() * 1000.0
        self.maximum = maximum
        # check for out of range selection at init time.
        if self.state > self.maximum:
            self.state = 0
        self.time_held = 0
        self.button_pressed = False
        self.long_press_time = 300
        self.output_period = 10 # output to csound pulse in ms
        self.led_period = 40 # output to csound pulse in ms
        #self.long_press_time = 63
        self.ignore_next_btrig = False
        self.name = name
        self.longtouch_cb = longtouch_cb
        self.inc_order = inc_order
        self.ignore_button = False
        self.ignore_gate = False
        self.trig_source = "button"
        ## hacky way for making sure LED stays low
        ## when file is >0 at bootup
        if name == "file":
            self.led_state = 0
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
            self.gate_switch = None
            self.gate_src = "NONE"
            self.button_src = "GPIO"
            self.button_switch = libSwitch.Switch(button_pin)
        elif button_gate_mode is BUTTON_SR_GATE_NONE:
            self.gate_switch = None
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

    def getTrigSource(self):
        return self.trig_source

    def getAction(self, state, prev_state, source):
        action = 0
        if self.edge == "rising" or source == "gate":
            if prev_state == 0 and state == 1:
                action = 1
        elif self.edge == "falling":
            if  prev_state == 1 and state == 0:
                action = 1
        return action

    def updateLongPress(self, raw_button):
        if self.edge == "falling":
            if raw_button == 1:
                self.button_pressed = True
                self.time_held = 0
            if self.button_pressed == True:
                self.time_held += 1
            if self.time_held > self.long_press_time:
                if self.longtouch_cb != None:
                    print "You long pressed a button"
                    self.longtouch_cb()
                self.time_held = 0
        
    def getRawValues(self, controltype, skip_update=False):
        if controltype == "gate":
            src = self.gate_src
            switch = self.gate_switch
            pin = self.gate_pin
        elif controltype == "button":
            src = self.button_src
            switch = self.button_switch
            pin = self.button_pin
        if src == "GPIO":
            if skip_update == False:
                switch.update()
            if switch.state() == True:
                state = 1
            else:
                state = 0
            if switch.prevState() == True:
                prev = 1
            else: 
                prev = 0
        elif src == "SR":
            if switch.state(pin) == True:
                state = 1
            else:
                state = 0
            if switch.prevState(pin) == True:
                prev = 1
            else: 
                prev = 0
            if controltype == "gate": # Flip for Hardware
                if state == 1:
                    state = 0
                else:
                    state = 1
                if prev == 1:
                    prev = 0
                else:
                    prev = 1
        elif src == "NONE":
            state = 0
            prev = 0 
            
        return state, prev
            

    def handle_button(self):
        if self.ignore_button == False:
            raw_button, raw_prev_button = self.getRawValues("button")
            action = self.getAction(raw_button, raw_prev_button, "button")
            if self.edge == "falling":
                self.updateLongPress(raw_button)
            if self.ignore_next_btrig == True:
                ### DOESNT AFFECT MOMENTARY
                if action == 1:
                    action = 0
                    self.ignore_next_btrig = False
                    self.time_held = 0
                    self.button_pressed = 0
            if self.mode == "triggered":
                if action == 1:
                    self.button_pulse_time = time.time() * 1000.0
                    self.b_state = 1
                if self.b_state == 1 and time.time() * 1000.0 - self.button_pulse_time > self.output_period:
                    self.b_state = 0
            elif self.mode == "latching":
                if action == 1:
                    self.b_state = 1
                else:
                    self.b_state = 0
            elif self.mode == "momentary":
                ### ONLY RISING
                if raw_button == 1: 
                    self.b_state = 1
                else:
                    self.b_state = 0
            elif self.mode == "incremental": 
                if action == 1:
                    self.b_state = 1
            #if self.ignore_button == True:
            #    self.b_state = 0

    def handle_gate(self):
        if "_alt" in self.name:
            self.ignore_gate = True
        if self.ignore_gate == False:
            raw_gate, raw_prev_gate = self.getRawValues("gate")
            action = self.getAction(raw_gate, raw_prev_gate, "gate")
            if self.mode == "triggered":
                #if self.g_state == 0 and raw_gate == 1:
                if action == 1:
                    self.gate_pulse_time = time.time() * 1000.0
                    self.g_state = 1
                if self.g_state == 1 and time.time() * 1000.0 - self.gate_pulse_time > self.output_period:
                    self.g_state = 0
            elif self.mode == "latching":
                if action == 1:
                #if raw_prev_gate == 0 and raw_gate == 1:
                    self.g_state = 1
                else:
                    self.g_state = 0
            elif self.mode == "momentary":
                if raw_gate == 1:
                    self.g_state = 1
                else:
                    self.g_state = 0
            elif self.mode == "incremental": 
                #if raw_gate == 1 and raw_prev_gate == 0:
                if action == 1:
                    self.g_state = 1
            #if self.ignore_gate == True:
            #    self.g_state = 0


    def handle_incremental_value(self):
        s = self.state
        g = self.g_state
        b = self.b_state
        self.g_state = 0
        self.b_state = 0
        if g == 1 or b == 1:
            if self.inc_order == 0:
                s += 1
                if s >= self.maximum:
                    s = 0
            elif self.inc_order == 1:
                s -= 1
                if s < 0:
                    s = self.maximum - 1
            elif self.inc_order == 2:
                s = random.randint(0, self.maximum - 1)
        if s > self.maximum:
            s = 0

        self.state = s
        
    def getValue(self):
        self.prev_state = self.state
        self.handle_button()
        self.handle_gate()
        if self.g_state == 1:
            self.trig_source = "gate"
        elif self.b_state == 1:
            self.trig_source = "button"
        if self.mode == "incremental":
            self.handle_incremental_value()
        elif self.mode == "momentary" or self.mode == "triggered":
            if self.g_state == 1 or self.b_state == 1:
                self.state = 1
            else:
                self.state = 0
        elif self.mode == "latching":
            if self.g_state == 1 or self.b_state == 1:
                self.g_state = 0
                self.b_state = 0
                if self.state == 1:
                    self.state = 0
                else:
                    self.state = 1
        return self.state

    def getLEDValue(self):
        if self.mode == "latching" or self.mode == "momentary":
            self.led_state = self.state
        if self.mode == "triggered":
            if self.state == 1 and self.prev_state == 0:
                self.led_pulse_time = time.time() * 1000.0
                self.led_state = 1
            if self.led_state == 1 and time.time() * 1000.0 - self.led_pulse_time > self.led_period:
                self.led_state = 0
        if self.mode == "incremental":
            raw_gate, raw_prev_gate = self.getRawValues("gate", skip_update=True)
            raw_button, raw_prev_button = self.getRawValues("button", skip_update=True)
            baction = self.getAction(raw_button, raw_prev_button, "button")
            gaction = self.getAction(raw_gate, raw_prev_gate, "gate")
            if baction == 1 or gaction == 1:
                self.led_pulse_time = time.time() * 1000.0
                self.led_state = 1
            if self.led_state == 1 and time.time() * 1000.0 - self.led_pulse_time > self.led_period:
                self.led_state = 0
        return self.led_state

####### BEGIN OG DIGITAL DATA
    def ogGetValue(self):
        if self.mode == "latching":
            if self.gate_src is "GPIO":
                self.gate_switch.update()
                g_trig = self.gate_switch.risingEdge()
            elif self.gate_src is "SR":
                g_trig = self.gate_switch.fallingEdge(self.gate_pin)
                #g_trig = self.gate_switch.risingEdge(self.gate_pin)

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
                if self.longtouch_cb != None:
                    if self.time_held > self.long_press_time and self.edge == "falling":
                        b_trig = False
                        self.ignore_next_btrig = True
                        self.button_pressed = False
                        self.time_held = 0
                        print "You long pressed a button!"
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
                if g_trig is True:
                    self.trig_source = "gate"
                elif b_trig is True:
                    self.trig_source = "button"
                if b_trig is True:
                    self.button_pressed = False
                    self.time_held = 0
                if self.state == 0:
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
                    if self.longtouch_cb is not None:
                        if self.time_held > self.long_press_time: 
                            if self.edge == "falling":
                                b_trig = False
                            self.button_pressed = False
                            self.time_held = 0
                            print "You long pressed a button!"
                            self.longtouch_cb()
                else:
                    if self.edge == "rising":
                        b_trig = self.button_switch.state(self.button_pin)
                    else:
                        b_trig = self.button_switch.state(self.button_pin)
                    if self.button_switch.risingEdge(self.button_pin) is True:
                        self.button_pressed = True
                        self.time_held = 0
                    if self.button_switch.fallingEdge(self.button_pin) is True:
                        self.button_pressed = False
                        self.time_held = 0
                    if self.button_pressed is True:
                        self.time_held += 1
                    if self.time_held > self.long_press_time: 
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
                if g_trig is True:
                    self.trig_source = "gate"
                elif b_trig is True:
                    self.trig_source = "button"
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
                if g_trig is True:
                    self.trig_source = "gate"
                elif b_trig is True:
                    self.trig_source = "button"
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
            if self.state >= self.maximum:
                self.state = 0
        elif self.mode == "momentary":
            if self.gate_src is "GPIO":
                self.gate_switch.update()
                g_trig = self.gate_switch.state()
            elif self.gate_src is "SR":
                g_trig = self.gate_switch.state(self.gate_pin)
            else:
                g_trig = False
            if self.ignore_gate is True:
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
            if self.ignore_button is True:
                b_trig = False
            if g_trig is True or b_trig is True or b_trig is 1:
                if g_trig is True:
                    self.trig_source = "gate"
                elif b_trig is True:
                    self.trig_source = "button"
                self.state = True
            else:
                self.state = False

        return self.state
####### END OG DIGITAL DATA
