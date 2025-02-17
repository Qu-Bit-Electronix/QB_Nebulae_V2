import RPi.GPIO as GPIO
import encoder as libEnc
import shiftregister as libSR
import leddriver as libDriver
import switch as libSwitch
import filehandler
import threading
import time
import random

sr_pin_next = 7
sr_pin_source_gate = 6
sr_pin_source = 5
sr_pin_freeze = 4
sr_pin_record = 3
sr_pin_reset = 0


class UserInterface(object):
    def __init__(self, controlhandler):
        self.controlhandler = controlhandler
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        self.currentInstr = None
        self.ledState = 1
        self.ledDriver = libDriver.LedDriver()
        self.pitch_click = libSwitch.Switch(22) # Pitch Encoder Click GPIO
        self.speed_click = libSwitch.Switch(26) # Speed Encoder Click GPIO
        # Set up Rotary Encoders
        self.encoder_pitch = libEnc.Encoder.Worker(17, 27)
        self.encoder_pitch.start() # Start Interrupt in a separate thread.
        self.encoder_speed = libEnc.Encoder.Worker(6, 13)
        self.encoder_speed.start() # Start Interrupt in a separate thread.
        self.pitch_delay = 0
        self.speed_delay = 0
        self.pitch_inc_dir = 0
        self.speed_inc_dir = 0
        self.encoder_delay_time = 500
        self.now = int(round(time.time() * 1000))
        self.pitch_blink_anim_flag = False
        self.pitch_blink_timer = self.now
        # Below are just the Blue on all RGB LEDs
        # Deltas for Encoders
        self.delta_p = 0
        self.delta_s = 0
        # Real Control Values (later share this with ControlHandler class
        self.speed_amount = self.controlhandler.getStaticVal("speed")
        self.alt_speed_amount = 23 # input level
        self.pitch_amount = self.controlhandler.getStaticVal("pitch")
        self.mode = "normal"

        user_dir = "/home/alarm/instr/"
        factory_dir = "/home/alarm/QB_Nebulae_V2/Code/instr/"
        pd_dir = "/home/alarm/pd/"
        self.factoryinstr_fhandle = filehandler.FileHandler(factory_dir, ".instr")
        self.userinstr_fhandle = filehandler.FileHandler(user_dir, ".instr")
        self.puredata_fhandle = filehandler.FileHandler(pd_dir, ".pd")
        cur_bank = self.controlhandler.getInstrSelBank()
        self.bank_shift_counter = 0
        if cur_bank == "factory":
            cnt = self.factoryinstr_fhandle.numFiles()
        elif cur_bank == "user":
            cnt = self.userinstr_fhandle.numFiles()
        elif cur_bank == "puredata":
            cnt = self.puredata_fhandle.numFiles()
        self.controlhandler.setInstrSelNumFiles(cnt)
        self.reload_flag = False # Flag to reload the whole program.
        self.alt_file_bright = 0.0
        self.alt_file_cnt = 0.0
        self.blink_counter = 0
        self.prev_blink = False
        self.blink = False
        self.time_pressed_pitch = self.now
        self.ignore_next_pitch_click = False
        self.ignore_next_speed_click = False
        self.clearAllLEDs()
        self.restoreDefaultsFlag = False

    def update(self):
        self.now = int(round(time.time() * 1000))
        if self.reload_flag == False:
            self.ledDriver.update()
        self.pitch_click.update()
        self.speed_click.update()
        self.delta_p = self.encoder_pitch.get_steps()
        self.delta_s = self.encoder_speed.get_steps()
        self.mode = self.controlhandler.mode()

        if self.mode == "secondary controls":
            if self.restoreDefaultsFlag == True:
                self.animateRestoration()
            elif self.controlhandler.getEditFunctionFlag("reset"):
                self.animateEditFunction("reset")
            else:
                #self.set_button_led("freeze", self.controlhandler.getAltValue("freeze_alt"))
                #self.set_button_led("source", self.controlhandler.getAltValue("source_alt"))
                #self.set_button_led("record", self.controlhandler.getAltValue("record_alt"))
                #self.set_button_led("reset", self.controlhandler.getAltValue("reset_alt"))
                self.set_button_led("freeze", self.controlhandler.getAltLEDValue("freeze_alt"))
                self.set_button_led("source", self.controlhandler.getAltLEDValue("source_alt"))
                self.set_button_led("record", self.controlhandler.getAltLEDValue("record_alt"))
                self.set_button_led("reset", self.controlhandler.getAltLEDValue("reset_alt"))
                if self.currentInstr == "a_granularlooper":
                    next_mode = self.controlhandler.getAltValue("file_alt")
                    self.setAltNextLed(next_mode)
                else:
                    self.set_button_led("next", self.controlhandler.getAltLEDValue("file_alt"))
        elif self.mode == "instr selector":
            self.displayInstrSel()
        else: # Includes Normal Behavior
            #self.set_button_led("freeze", self.controlhandler.getValue("freeze"))
            #self.set_button_led("source", self.controlhandler.getValue("source"))
            #self.set_button_led("record", self.controlhandler.getValue("record"))
            #next_state = self.controlhandler.shiftReg.state(sr_pin_next)
            #next_gate_state = not GPIO.input(23)
            #if next_state == 1 or next_gate_state == 1:
            #    self.set_button_led("next", 1)
            #else:
            #    self.set_button_led("next", 0)
            self.set_button_led("freeze", self.controlhandler.getLEDValue("freeze"))
            self.set_button_led("source", self.controlhandler.getLEDValue("source"))
            self.set_button_led("record", self.controlhandler.getLEDValue("record"))
            self.set_button_led("next", self.controlhandler.getLEDValue("file"))
            if self.controlhandler.getEditFunctionFlag("reset") == True:
                self.animateEditFunction("reset")
            elif self.controlhandler.getEditFunctionFlag("record") == True:
                self.animateEditFunction("record")
            elif self.controlhandler.getEditFunctionFlag("source") == True:
                self.animateEditFunction("source")
                if self.controlhandler.currentBank == 'factory':
                    tempidx = self.factoryinstr_fhandle.getIndex(self.controlhandler.currentInstr)
                elif self.controlhandler.currentBank == 'user':
                    tempidx = self.userinstr_fhandle.getIndex(self.controlhandler.currentInstr)
                elif self.controlhandler.currentBank == 'puredata':
                    tempidx = self.puredatainstr_fhandle.getIndex(self.controlhandler.currentInstr)
                self.controlhandler.setInstrSelIdx(tempidx)
                self.controlhandler.setInstrSelBank(self.controlhandler.currentBank)
                # self.controlhandler.settings.update(self.now)
                # self.controlhandler.settings.write()
                self.reload_flag = True
            elif self.controlhandler.writing_buffer == True:
                self.animateBufferWrite()
            elif self.controlhandler.buffer_failure == True:
                self.animateBufferFailure()
                #self.animateEditFunction("freeze")
            else:
                if self.currentInstr == "a_granularlooper":
                    if self.controlhandler.size_status_comm.getState() == 0:
                        #self.set_button_led("reset", self.controlhandler.getEndOfLoopState())
                        if self.controlhandler.eol_comm.getState() > 0:
                            self.set_button_led("reset", 1.0)
                        else:
                            self.set_button_led("reset", 0.0)
                    else:
                        self.set_button_led("reset", 1.0)
                else:
                    state = self.controlhandler.getLEDValue("reset")
                    if state == True or state == 1:
                        self.set_button_led("reset", 1.0)
                    else:
                        self.set_button_led("reset", 0.0)

        self.update_speed(self.mode)
        self.update_pitch(self.mode)

    def clearAllLEDs(self):
        self.set_rgb("pitch_pos", 4095, 4095, 4095, 0.0)
        self.set_rgb("pitch_neg", 4095, 4095, 4095, 0.0)
        self.set_rgb("speed_pos", 4095, 4095, 4095, 0.0)
        self.set_rgb("speed_neg", 4095, 4095, 4095, 0.0)
        self.set_button_led("reset", 0.0)
        self.set_button_led("record", 0.0)
        self.set_button_led("freeze", 0.0)
        self.set_button_led("source", 0.0)
        self.set_button_led("next", 0.0)

    def displayInstrSel(self):
        values = [0, 0, 0, 0, 0]
        blink = (self.now & 500) > 250
        low_bright = 0.3
        if self.controlhandler.getInstrSelBank() == "factory":
            f_handle = self.factoryinstr_fhandle
        elif self.controlhandler.getInstrSelBank() == "user":
            f_handle = self.userinstr_fhandle
        elif self.controlhandler.getInstrSelBank() == "puredata":
            f_handle = self.puredata_fhandle
        idx = self.controlhandler.getInstrSelIdx()
        offset = self.controlhandler.getInstrSelOffset()
        for i in range(0, 5):
            if i < f_handle.numFiles():
                values[i] = low_bright
        #if idx >= offset and idx < offset + 4:
        #    led = idx - offset
        #    values[led] = 1
        led = idx - offset
        if led >= 0 and led <= 4:
            values[led] = 1
        if offset > 0:
            if blink == True:
                if idx == offset: #bright blink
                    val = 1.0
                else:
                    val = 0.0
            else:
                if idx < offset:
                    val = 1.0
                else:
                    val = low_bright
            values[0] = val
        if offset + 5 < f_handle.numFiles():
            if blink == True:
                if idx == offset + 4: #bright blink
                    val = 1.0
                else:
                    val = 0.0
            else:
                if idx > offset + 4:
                    val = 1.0
                else:
                    val = low_bright
            values[4] = val

        #print "Instr Sel Bank: " + self.controlhandler.getInstrSelBank()
        #print "Instr Sel Num files: " + str(f_handle.numFiles())
        #s = f_handle.getFilename(idx)
        #if s is not None:
            #print "File Name: " + f_handle.getFilename(idx)
        #else:
            #print "No File Here"
        self.set_button_led("record", values[0])
        self.set_button_led("next", values[1])
        self.set_button_led("source", values[2])
        self.set_button_led("reset", values[3])
        self.set_button_led("freeze", values[4])

    def animateEditFunction(self, name):
        ## TODO: The abstraction could actually do this animation for any of the four buttons (file, source, reset, freeze)
        if self.controlhandler.getEditFunctionFlag(name) == True:
            if self.blink_counter < 5:
                self.prev_blink = self.blink
                self.blink = (self.now & 100) < 50
                if self.blink == False and self.prev_blink == True:
                    self.blink_counter += 1
                if self.blink == True:
                    self.set_button_led(name, 1)
                else:
                    self.set_button_led(name, 0)
            else:
                self.controlhandler.clearEditFunctionFlag(name)
                self.blink_counter = 0
                self.set_button_led(name, 0)
        else:
            self.prev_blink = self.blink
            self.blink = False

    def animateBufferWrite(self):
        self.prev_blink = self.blink
        self.blink = (self.now & 500) < 250
        if self.blink == True:
            self.set_button_led("freeze", 1)
            self.set_button_led("record", 1)
        else:
            self.set_button_led("freeze", 0)
            self.set_button_led("record", 0)

    def animateBufferFailure(self):
        self.prev_blink = self.blink
        if (self.controlhandler.buffer_failure == True):
            if self.blink_counter < 10:
                self.blink = (self.now & 250) < 125
                if self.blink == True:
                    if self.prev_blink == False:
                        self.blink_counter += 1
                    self.set_button_led("record", 1)
                    self.set_button_led("next", 1)
                    self.set_button_led("source", 1)
                    self.set_button_led("reset", 1)
                    self.set_button_led("freeze", 1)
                else:
                    self.set_button_led("record", 0)
                    self.set_button_led("next", 0)
                    self.set_button_led("source", 0)
                    self.set_button_led("reset", 0)
                    self.set_button_led("freeze", 0)
            else:
                self.controlhandler.buffer_failure = False
                self.blink_counter = 0
                self.set_button_led("record", 0)
                self.set_button_led("next", 0)
                self.set_button_led("source", 0)
                self.set_button_led("reset", 0)
                self.set_button_led("freeze", 0)
        else:
            self.blink = False

    def animateRestoration(self):
        ## TODO: The abstraction could actually do this animation for any of the four buttons (file, source, reset, freeze)
        if self.blink_counter < 4:
            self.prev_blink = self.blink
            self.blink = (self.now & 100) < 50
            if self.blink == False and self.prev_blink == True:
                self.blink_counter += 1
            for name in ["reset", "record", "next", "source", "freeze"]:
                if self.blink == True:
                    self.set_button_led(name, 1)
                else:
                    self.set_button_led(name, 0)
        else:
            #self.controlhandler.clearEditFunctionFlag(name)
            self.restoreDefaultsFlag = False
            self.blink_counter = 0
            for name in ["reset", "record", "file", "source", "freeze"]:
                self.set_button_led(name, 0)

    def pressed_pitch(self):
        return self.pitch_click.state()

    def pressed_speed(self):
        return self.speed_click.state()


    def clicked_pitch(self):
        if self.pitch_click.fallingEdge():
            if self.ignore_next_pitch_click == False:
                return 1
            else:
                self.ignore_next_pitch_click = False
                return 0
        else:
            return 0

    def clicked_speed(self):
        if self.speed_click.fallingEdge():
            if self.ignore_next_speed_click == False:
                return 1
            else:
                self.ignore_next_speed_click = False
                return 0
        else:
            return 0

    def get_delta(self, name):
        if name == "speed":
            return self.delta_s
        elif name == "pitch":
            return self.delta_p
        else:
            return None

    def set_speed_amount(self):
        self.speed_amount = self.controlhandler.getStaticVal("speed")
        inc = self.get_delta("speed")
        if self.speed_click.state() == True:
            inc = 0
        if self.speed_delay == -1:
            if inc > 0:
                if self.speed_inc_dir == 1:
                    self.speed_amount += 0.001 * inc * inc * inc
                    self.speed_inc_dir = 1
                else:
                    self.speed_inc_dir = 1
            elif inc < 0:
                if self.speed_inc_dir == -1:
                    self.speed_amount -= 0.001 * (-1 * inc) * (-1 * inc) * (-1 * inc)
                    self.speed_inc_dir = -1
                else:
                    self.speed_inc_dir = -1
        else:
            if self.now > self.speed_delay:
                self.speed_delay = -1
        if self.speed_amount > 1.0:
            self.speed_amount = 1.0
        elif self.speed_amount < 0.0:
            self.speed_amount = 0.0
        if self.clicked_speed() == 1:
            self.speed_delay = self.now + self.encoder_delay_time
            if (self.speed_amount > 0.62 and self.speed_amount < 0.63):
                self.speed_amount = .375
            else:
                self.speed_amount = .625
        self.controlhandler.setValue("speed", self.speed_amount)

    def set_alt_speed_amount(self):
        self.alt_speed_amount = self.controlhandler.getAltValue("speed_alt")
        inc = self.get_delta("speed")
        if inc > 0:
            self.alt_speed_amount += 1
        elif inc < 0:
            self.alt_speed_amount -= 1
        if self.alt_speed_amount > 32:
            self.alt_speed_amount = 32
        elif self.alt_speed_amount < 0:
            #self.alt_speed_amount = 0.0
            self.alt_speed_amount = 0
        if self.clicked_speed() == 1:
            #self.alt_speed_amount = 0.710 # 23/32 = 0dB input gain
            self.alt_speed_amount = 23
        self.controlhandler.setAltValue("speed_alt", self.alt_speed_amount)

    # Returns duple of neg_brightness, pos_brightness
    def set_speed_leds(self, mode):
        if mode == "normal" or mode == "puredata":
            pink = libDriver.Color(3037, 200, 3825)
            white = libDriver.Color(4095,4095,4095)
            red = libDriver.Color(4095, 0, 0) #octave 0 / record
            orange = libDriver.Color(4095, 1100, 0) #octave 1 (1V)
            yellow = libDriver.Color(4095, 3395, 0) #octave 2 (2V)
            blue = libDriver.Color(0,0,4095) #octave 3 (3V original pitch)
            green = libDriver.Color(0, 4095, 0) # octave 4 (4V)
            purple = libDriver.Color(511, 0, 4095) # octave 5 (5V)
            colororder = [ white, orange, yellow, blue, green, purple]
            speed_amt = self.controlhandler.channeldict["speed"].curVal
            translated_speed = speed_amt * 8.0 - 4.0
            factors = [0.125, 0.25, 0.5, 1.0, 2.0, 4.0]
            color_pos = white
            color_neg = white
            #speed_pos_bright = (speed_amt - 0.5) * 2.0
            #speed_neg_bright = ((1.0 - speed_amt) - 0.5) * 2.0
            if translated_speed > 0:
                speed_pos_bright = 1.0
                speed_neg_bright = 0.0
            else:
                speed_pos_bright = 0.0
                speed_neg_bright = 1.0
            speed_pos_bright *= 0.33
            speed_neg_bright *= 0.33
            blink = (self.now & 150) > 75
            highest_factor = 0
            abs_speed = abs(translated_speed)
            if abs_speed < factors[0]:
                highest_factor = 0
            elif abs_speed < factors[1]:
                highest_factor = 1
            elif abs_speed < factors[2]:
                highest_factor = 2
            elif abs_speed < factors[3]:
                highest_factor = 3
            elif abs_speed < factors[4]:
                highest_factor = 4
            elif abs_speed < factors[5]:
                highest_factor = 5

            if highest_factor < 1:
                scalar = (abs_speed / factors[0])
                newcolor = colororder[0]
                color_pos = newcolor
                color_neg = newcolor
                if translated_speed < 0:
                    speed_neg_bright = scalar * 0.33
                else:
                    speed_pos_bright = scalar * 0.33
            else:
                scalarRange = factors[highest_factor] / 2.0
                scalar = (abs_speed - factors[highest_factor - 1]) / scalarRange
                newcolor = self.blendColor(colororder[highest_factor-1], colororder[highest_factor], scalar)
                color_pos = newcolor
                color_neg = newcolor
            for idx, factor in enumerate(factors):
                if (abs(translated_speed) > factor - 0.0075) and abs(translated_speed) < factor + 0.0075:
                    if translated_speed > 0:
                        color_pos = colororder[idx]
                        speed_pos_bright = 1.0
                    else:
                        color_neg = colororder[idx]
                        speed_neg_bright = 1.0
            if translated_speed == 0:
                speed_pos_bright = 0
                speed_neg_bright = 0
            if speed_pos_bright < 0:
                speed_pos_bright = 0
            if speed_neg_bright < 0:
                speed_neg_bright = 0
            if self.currentInstr == "a_granularlooper":
                if self.controlhandler.channeldict["record"].curVal == 1:
                    color_neg = red
                    color_pos = red
                    speed_neg_bright = 1.0
                    speed_pos_bright = 1.0
            self.set_rgb("speed_neg", color_neg.red(), color_neg.green(),color_neg.blue(), speed_neg_bright)
            self.set_rgb("speed_pos", color_pos.red(), color_pos.green(),color_pos.blue(), speed_pos_bright)
        elif mode == "secondary controls":
            speed_ticks  = self.controlhandler.getAltValue("speed_alt")
            speed_amt = speed_ticks / 32.0
            speed_pos_bright = (speed_amt - 0.5) * 2.0
            speed_neg_bright = ((1.0 - speed_amt) - 0.5) * 2.0
            if speed_pos_bright < 0:
                speed_pos_bright = 0
            if speed_neg_bright < 0:
                speed_neg_bright = 0
            if speed_ticks == 23:
                tempc = libDriver.Color(0, 4095, 0)
            else:
                tempc = libDriver.Color(3037, 200, 3825)
            self.set_rgb("speed_neg", tempc.red(), tempc.green(), tempc.blue(), speed_neg_bright)
            self.set_rgb("speed_pos", tempc.red(), tempc.green(), tempc.blue(), speed_pos_bright)
        elif mode == "instr selector":
            tempc = libDriver.Color(0, 4095, 0)
            if self.controlhandler.getInstrSelBank() == "factory":
                self.set_rgb("speed_neg", tempc.red(), tempc.green(), tempc.blue(), 1.0)
                self.set_rgb("speed_pos", tempc.red(), tempc.green(), tempc.blue(), 1.0)
            elif self.controlhandler.getInstrSelBank() == "user":
                self.set_rgb("speed_neg", tempc.red(), tempc.green(), tempc.blue(), 1.0)
                self.set_rgb("speed_pos", tempc.red(), tempc.green(), tempc.blue(), 0.0)
            elif self.controlhandler.getInstrSelBank() == "puredata":
                self.set_rgb("speed_neg", tempc.red(), tempc.green(), tempc.blue(), 0.0)
                self.set_rgb("speed_pos", tempc.red(), tempc.green(), tempc.blue(), 1.0)
        else:
            pass

    def update_speed(self, mode):
        if mode == "normal" or mode == "puredata":
            if self.speed_click.risingEdge() == True:
                self.time_pressed_speed = self.now
            if self.speed_click.state() == True and self.now - self.time_pressed_speed > 1500:
                self.ignore_next_speed_click = True
                self.controlhandler.enterInstrSelMode()
            self.set_speed_amount()
        elif mode == "puredata":
            if self.speed_click.risingEdge() == True:
                self.time_pressed_speed = self.now
            if self.speed_click.state() == True and self.now - self.time_pressed_speed > 1500:
                self.ignore_next_speed_click = True
                self.controlhandler.enterInstrSelMode()
            self.set_speed_amount()
        elif mode == "secondary controls":
            self.set_alt_speed_amount()
        elif mode == "instr selector":
            # Set Bank
            cur_bank = self.controlhandler.getInstrSelBank()
            inc = self.get_delta("speed")
            thresh = 8
            self.bank_shift_counter += inc
            if self.bank_shift_counter > thresh:
                self.bank_shift_counter = thresh
            elif self.bank_shift_counter < -1 * thresh:
                self.bank_shift_counter = -1 * thresh

            #print "bank shift counter: " + str(self.bank_shift_counter)


            if cur_bank == "user" and self.bank_shift_counter >= thresh:
                self.bank_shift_counter = 0
                self.controlhandler.setInstrSelBank("factory")
                self.controlhandler.setInstrSelNumFiles(self.factoryinstr_fhandle.numFiles())
            elif cur_bank == "puredata" and self.bank_shift_counter <= -1 * thresh:
                self.bank_shift_counter = 0
                self.controlhandler.setInstrSelBank("factory")
                self.controlhandler.setInstrSelNumFiles(self.factoryinstr_fhandle.numFiles())
            elif cur_bank == "factory":
                if self.bank_shift_counter >= thresh:
                    self.bank_shift_counter = 0
                    self.controlhandler.setInstrSelBank("puredata")
                    self.controlhandler.setInstrSelNumFiles(self.puredata_fhandle.numFiles())
                elif self.bank_shift_counter <=  -1 * thresh:
                    self.bank_shift_counter = 0
                    self.controlhandler.setInstrSelBank("user")
                    self.controlhandler.setInstrSelNumFiles(self.userinstr_fhandle.numFiles())

            if self.clicked_speed() == 1:
                print "Clicked Speed from Instr Sel"
                self.reload_flag = True
        else:
            pass
        self.set_speed_leds(mode)

    def set_pitch_amount(self):
        self.pitch_amount = self.controlhandler.getStaticVal("pitch")
        inc = self.get_delta("pitch")
        inc_size = 0.001
        if self.pitch_click.state() == True:
            #inc = 0
            inc_size = 0.2
        if self.pitch_delay == -1:
            if inc > 0:
                if self.pitch_inc_dir == 1:
                    if inc_size == 0.2:
                        self.ignore_next_pitch_click = True
                        self.pitch_delay = self.now + 125
                    self.pitch_amount += inc_size * inc * inc * inc
                    self.pitch_inc_dir = 1
                else:
                    self.pitch_inc_dir = 1
            elif inc < 0:
                if self.pitch_inc_dir == -1:
                    if inc_size == 0.2:
                        self.ignore_next_pitch_click = True
                        self.pitch_delay = self.now + 125
                    self.pitch_amount -= inc_size * (-1 * inc) * (-1 * inc) * (-1 * inc)
                    self.pitch_inc_dir = -1
                else:
                    self.pitch_inc_dir = -1
        else:
            if self.now > self.pitch_delay:
                self.pitch_delay = -1
        if self.pitch_amount > 1.0:
            self.pitch_amount = 1.0
        elif self.pitch_amount < 0:
            self.pitch_amount = 0.0
        if self.clicked_pitch() == 1:
            self.pitch_delay = self.now + self.encoder_delay_time
            self.pitch_amount = 0.60
        self.controlhandler.setValue("pitch", self.pitch_amount)

    def set_alt_pitch_amount(self):
        self.alt_pitch_amount = self.controlhandler.getAltStaticVal("pitch_alt")
        inc = self.get_delta("pitch")
        if inc > 0:
            self.alt_pitch_amount += 0.002 * inc
        elif inc < 0:
            self.alt_pitch_amount -= 0.002 * (-1 * inc)
        if self.pitch_click.state() == True:
            inc = 0
        if self.pitch_delay == -1:
            if inc > 0:
                if self.pitch_inc_dir == 1:
                    self.alt_pitch_amount += 0.001 * inc * inc * inc
                    self.pitch_inc_dir = 1
                else:
                    self.pitch_inc_dir = 1
            elif inc < 0:
                if self.pitch_inc_dir == -1:
                    self.alt_pitch_amount -= 0.001 * (-1 * inc) * (-1 * inc) * (-1 * inc)
                    self.pitch_inc_dir = -1
                else:
                    self.pitch_inc_dir = -1
        else:
            if self.now > self.pitch_delay:
                self.pitch_delay = -1
        if self.alt_pitch_amount > 1.0:
            self.pitch_blink_anim_flag = True
            self.pitch_blink_timer = self.now
            self.alt_pitch_amount = 1.0
        elif self.alt_pitch_amount < 0:
            self.pitch_blink_anim_flag = True
            self.pitch_blink_timer = self.now
            self.alt_pitch_amount = 0.0
        self.controlhandler.setAltValue("pitch_alt", self.alt_pitch_amount)

    def set_pitch_leds(self, mode):
        # Pitch input 0-1.0 neg | 1.0-4.0 pos
        pink = libDriver.Color(3037, 200, 3825)
        white = libDriver.Color(4095,4095,4095)
        red = libDriver.Color(4095, 0, 0) #octave 0 / record
        orange = libDriver.Color(4095, 1100, 0) #octave 1 (1V)
        yellow = libDriver.Color(4095, 3395, 0) #octave 2 (2V)
        blue = libDriver.Color(0,0,4095) #octave 3 (3V original pitch)
        green = libDriver.Color(0, 4095, 0) # octave 4 (4V)
        purple = libDriver.Color(511, 0, 4095) # octave 5 (5V)
        colororder = [ white, orange, yellow, blue, green, purple]
        octaves = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        if mode == "normal" or mode == "puredata":
            original_pitch = 0.6
            tolerance = 0.001
            pitch_amt = round(self.controlhandler.getValue("pitch"), 4) # I don't like that I have to do this
            sector_total = pitch_amt / 0.2
            sector_int = int(sector_total)
            sector_brightness = sector_total - sector_int
            if pitch_amt > original_pitch + tolerance:
                # handle blending up ward
                if pitch_amt > octaves[5]:
                    scalar = (pitch_amt - octaves[5]) * 5.00
                    pos_color = self.blendColor(colororder[5], colororder[0], scalar)
                elif pitch_amt > octaves[4]:
                    ## Blend green to purple
                    scalar = (pitch_amt - octaves[4]) * 5.00
                    pos_color = self.blendColor(colororder[4], colororder[5], scalar)
                else:
                    scalar = (pitch_amt - octaves[3]) * 5.00
                    pos_color = self.blendColor(colororder[3], colororder[4], scalar)
                neg_color = white
                #pitch_pos_bright = sector_brightness * 0.33
                pitch_pos_bright = 0.33
                pitch_neg_bright = 0.0
            elif pitch_amt < original_pitch - tolerance:
                if pitch_amt < octaves[1]:
                    scalar = (pitch_amt - octaves[0]) * 5.0
                    neg_color = self.blendColor(colororder[0], colororder[1], scalar)
                elif pitch_amt < octaves[2]:
                    scalar = (pitch_amt - octaves[1]) * 5.0
                    neg_color = self.blendColor(colororder[1], colororder[2], scalar)
                elif pitch_amt < octaves[3]:
                    scalar = (pitch_amt - octaves[2]) * 5.0
                    neg_color = self.blendColor(colororder[2], colororder[3], scalar)
                pos_color = white
                pitch_pos_bright = 0.0
                pitch_neg_bright = 0.33
            octaves = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
            for idx, octave in enumerate(octaves):
                if pitch_amt >= octave - tolerance and pitch_amt <= octave + tolerance:
                    if octave < 0.6:
                        pitch_neg_bright = 1.0
                        neg_color = colororder[idx]
                    elif octave > 0.6:
                        pitch_pos_bright = 1.0
                        pos_color = colororder[idx]
                    else:
                        pitch_pos_bright = 1.0
                        pitch_neg_bright = 1.0
                        pos_color = colororder[idx]
                        neg_color = colororder[idx]
            self.set_rgb("pitch_neg", neg_color.red(), neg_color.green(),neg_color.blue(), pitch_neg_bright)
            self.set_rgb("pitch_pos", pos_color.red(), pos_color.green(),pos_color.blue(), pitch_pos_bright)
        elif mode == "secondary controls":
            tempc = purple
            amt = round(self.controlhandler.getAltValue("pitch_alt"), 3)

            pos_bright = (amt - 0.5) * 2.0
            neg_bright = ((1.0 - amt) - 0.5) * 2.0
            if pos_bright < 0.0:
                pos_bright = 0.0
            elif pos_bright > 1.0:
                pos_bright = 1.0
            if neg_bright < 0.0:
                neg_bright = 0.0
            elif neg_bright > 1.0:
                neg_bright = 1.0
            blink = (self.now & 150) > 75
            if amt < 0.001 and self.pitch_blink_anim_flag == True:
                if blink == True:
                    neg_bright = 1.0
                else:
                    neg_bright = 0.0
                    if self.now - self.pitch_blink_timer > 450:
                        self.pitch_blink_anim_flag = False
            if amt > 0.99 and self.pitch_blink_anim_flag == True:
                if blink == True:
                    pos_bright = 1.0
                else:
                    pos_bright = 0.0
                    if self.now - self.pitch_blink_timer > 450:
                        self.pitch_blink_anim_flag = False
            self.set_rgb("pitch_neg", tempc.red(), tempc.green(), tempc.blue(), neg_bright)
            self.set_rgb("pitch_pos", tempc.red(), tempc.green(), tempc.blue(), pos_bright)
        elif mode == "instr selector":
            tempc = libDriver.Color(0, 4095, 0)
            self.set_rgb("pitch_neg", tempc.red(), tempc.green(), tempc.blue(), 1.0)
            self.set_rgb("pitch_pos", tempc.red(), tempc.green(), tempc.blue(), 1.0)
        else:
            pass


    def update_pitch(self, mode):
        if mode == "normal" or mode == "puredata":
            if self.pitch_click.risingEdge() == True:
                self.time_pressed_pitch = self.now
            self.set_pitch_amount()
        elif mode == "secondary controls":
            self.set_alt_pitch_amount()
            if self.pitch_click.risingEdge() == True:
                self.restoreDefaultsFlag = True
                self.controlhandler.restoreAltToDefault()
        elif mode == "instr selector":
            if self.controlhandler.getInstrSelBank() == "factory":
                f_handle = self.factoryinstr_fhandle
            elif self.controlhandler.getInstrSelBank() == "user":
                f_handle = self.userinstr_fhandle
            elif self.controlhandler.getInstrSelBank() == "puredata":
                f_handle = self.puredata_fhandle
            if f_handle.numFiles() <= 5:
                offset = 0
            else:
                offset = self.controlhandler.getInstrSelOffset()
                inc = self.get_delta("pitch")
                offset += inc
                if offset >= (f_handle.numFiles() - 5):
                    offset = f_handle.numFiles() - 5
                if offset < 0:
                    offset = 0
                self.controlhandler.setInstrSelOffset(offset)
        else:
            pass

        if mode == "instr selector":
            if self.clicked_pitch():
                #print "current Instr: " + str(self.currentInstr)
                #print "all files in puredata_fhandle:"
                #l = self.puredata_fhandle.getFileNames()
                #for name in l:
                #    print name
                if self.currentInstr in self.puredata_fhandle.getFileNames():
                    self.controlhandler.enterPureDataMode()
                else:
                    self.controlhandler.enterNormalMode()
        self.set_pitch_leds(mode)

    def set_rgb(self, name, r, g, b, bright=1.0):
        self.ledDriver.set_rgb(name, r, g, b, bright)

    def set_button_led(self, name, bright):
        self.ledDriver.set_button_led(name, bright)

    def cleanup(self):
        self.encoder_pitch.stop()
        self.encoder_speed.stop()
        self.ledDriver.cleanup()
        GPIO.cleanup()

    def getReloadRequest(self):
        return self.reload_flag

    def setAltNextLed(self, mode):
        fade_inc = 0.009
        if mode == 0:
            self.alt_file_bright += fade_inc
            if self.alt_file_bright > 1.0:
                self.alt_file_bright = 0.0
        elif mode == 1:
            self.alt_file_bright -= fade_inc
            if self.alt_file_bright < 0.0:
                self.alt_file_bright = 1.0
        elif mode == 2:
            self.alt_file_cnt += fade_inc
            if self.alt_file_cnt > 0.2:
                self.alt_file_cnt = 0.0
                self.alt_file_bright = random.random()
        self.set_button_led("next", self.alt_file_bright)

    def getNewInstr(self):
        idx = self.controlhandler.getInstrSelIdx()
        if self.controlhandler.getInstrSelBank() == "factory":
            if idx < self.factoryinstr_fhandle.numFiles():
                instr = self.factoryinstr_fhandle.getFilename(idx)
        elif self.controlhandler.getInstrSelBank() == "user":
            if idx < self.userinstr_fhandle.numFiles():
                instr = self.userinstr_fhandle.getFilename(idx)
        elif self.controlhandler.getInstrSelBank() == "puredata":
            if idx < self.puredata_fhandle.numFiles():
                instr = self.puredata_fhandle.getFilename(idx)
        return instr

    def setCurrentInstr(self, instr):
        self.currentInstr = instr
        self.controlhandler.setCurrentInstr(instr)
        handlers = [self.factoryinstr_fhandle, self.userinstr_fhandle, self.puredata_fhandle]
        tempbank = None
        for handle in handlers:
            tempidx = handle.getIndex(instr)
            if tempidx is not None:
                tempbank = handle
                if tempbank == self.factoryinstr_fhandle:
                    tempbankname = "factory"
                elif tempbank == self.userinstr_fhandle:
                    tempbankname = "user"
                elif tempbank == self.puredata_fhandle:
                    tempbankname = "puredata"
                break
        # Only udpate if the instr is found
        if tempidx is not None and tempbank is not None:
            if tempidx < 5:
                self.controlhandler.setInstrSelIdx(tempidx)
                self.controlhandler.setInstrSelOffset(0)
            else:
                self.controlhandler.setInstrSelIdx(tempidx % 5)
                self.controlhandler.setInstrSelOffset(tempidx / 5)
            self.controlhandler.setInstrSelBank(tempbankname)

    def blendColor(self, color_a, color_b, amount):
        newred = (color_a.red() * (1.0 - amount)) + (color_b.red() * amount)
        newgreen = (color_a.green() * (1.0 - amount)) + (color_b.green() * amount)
        newblue = (color_a.blue() * (1.0 - amount)) + (color_b.blue() * amount)
        return libDriver.Color(newred, newgreen, newblue) # defaults to white.
