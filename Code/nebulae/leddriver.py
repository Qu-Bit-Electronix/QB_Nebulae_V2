# leddriver.py
# Stephen Hensley
# Interfacing Class for PCA9685 LED Driver

import Adafruit_PCA9685
import RPi.GPIO as GPIO
import threading

# Delclarations of Address Pins for our LEDs
ADDR_PITCH_POS_R = 8
ADDR_PITCH_POS_G = 0
ADDR_PITCH_POS_B = 1
ADDR_PITCH_NEG_R = 13
ADDR_PITCH_NEG_G = 15
ADDR_PITCH_NEG_B = 14
ADDR_SPEED_POS_R = 4
ADDR_SPEED_POS_G = 3
ADDR_SPEED_POS_B = 2
ADDR_SPEED_NEG_R = 7
ADDR_SPEED_NEG_G = 5
ADDR_SPEED_NEG_B = 6
ADDR_RECORD = 9
ADDR_NEXT = 10
ADDR_SOURCE = 11
ADDR_FREEZE = 12

RESET_LED_PIN = 12
# Simple Class For Holding three integers of data for colors
class Color(object):
    def __init__(self, r=4095, g=4095, b=4095):
        self.r = r
        self.g = g
        self.b = b

    def red(self):
        return self.r

    def green(self):
        return self.g

    def blue(self):
        return self.b

class RGBLed(object):
    def __init__(self, device, addr_r, addr_g, addr_b):
        self.device = device
        self.addr_r = addr_r
        self.addr_g = addr_g
        self.addr_b = addr_b
        self.color = Color()
        self.brightness = 1.0
        self.prev_brightness = 1.0
        self.change_flag = False

    def set_color(self, color):
        self.prev_color = self.color
        self.color = color
        if self.prev_color != self.color:
            self.change_flag = True

    def set_brightness(self, brightness):
        self.prev_brightness = self.brightness
        self.brightness = brightness
        if self.prev_brightness != self.brightness:
            self.change_flag = True

    def post_brightness_color(self):
        red = int(self.color.red() * self.brightness)
        green = int(self.color.green() * self.brightness)
        blue = int(self.color.blue() * self.brightness)
        col = Color(red, green, blue)
        return col

    def update(self):
        #if self.change_flag is True:
        dim_color = self.post_brightness_color()
        self.device.set_pwm(self.addr_r, 0, 4095 - dim_color.red())
        self.device.set_pwm(self.addr_g, 0, 4095 - dim_color.green())
        self.device.set_pwm(self.addr_b, 0, 4095 - dim_color.blue())

class ButtonLed(object):
    def __init__(self, device, addr):
        self.device = device
        self.addr = addr
        self.brightness = 0.0
        self.prev_brightness = 0.0

    def set_brightness(self, brightness):
        self.prev_brightness = self.brightness 
        self.brightness = 1.0 - brightness

    def get_int_brightness(self):
        value = int(self.brightness * 4095)
        return value

    def update(self):
        #if self.brightness != self.prev_brightness:
        self.device.set_pwm(self.addr, 0, self.get_int_brightness())

class GPIOLed(object):
    def __init__(self, pin):
        self.pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, True)
        self.pwm = GPIO.PWM(self.pin, 150)
        self.pwm.stop()
        self.brightness = 0.0
        self.prev_brightness = 0.0
        self.pwm.start(100)
        self.value = 0

    def set_brightness(self, brightness):
        self.prev_brightness = self.brightness
        self.brightness = 1.0 - brightness
        self.pwm.ChangeDutyCycle(int(self.brightness * 100))

    def update(self):
        pass
        #print "I'm the reset LED updating to: " + str(self.brightness)
        #self.pwm.ChangeDutyCycle(int(self.brightness * 100))

    def set(self, state):
        pass
        #if state == 1:
        #    GPIO.output(self.pin, False)
        #else:
            #GPIO.output(self.pin, True)

    def cleanup(self):
        pass
        #self.pwm.stop()
       
class LedDriver(object):
    def __init__(self):
        self.device = Adafruit_PCA9685.PCA9685()
        self.device.set_pwm_freq(250)
        self.ledRecord = ButtonLed(self.device, ADDR_RECORD)
        self.ledNext = ButtonLed(self.device, ADDR_NEXT)
        self.ledSource = ButtonLed(self.device, ADDR_SOURCE)
        self.ledFreeze = ButtonLed(self.device, ADDR_FREEZE)
        self.ledReset = GPIOLed(RESET_LED_PIN)
        self.ledPitchPos = RGBLed(self.device, ADDR_PITCH_POS_R, ADDR_PITCH_POS_G, ADDR_PITCH_POS_B)
        self.ledPitchNeg = RGBLed(self.device, ADDR_PITCH_NEG_R, ADDR_PITCH_NEG_G, ADDR_PITCH_NEG_B)
        self.ledSpeedPos = RGBLed(self.device, ADDR_SPEED_POS_R, ADDR_SPEED_POS_G, ADDR_SPEED_POS_B)
        self.ledSpeedNeg = RGBLed(self.device, ADDR_SPEED_NEG_R, ADDR_SPEED_NEG_G, ADDR_SPEED_NEG_B)
        self.current_led = 0
        self.ledList = [self.ledRecord, self.ledNext, self.ledSource, self.ledFreeze, self.ledReset,
                        self.ledPitchPos, self.ledPitchNeg, self.ledSpeedPos, self.ledSpeedNeg]


    def update(self):
        self.ledList[self.current_led].update()
        if self.current_led < len(self.ledList) - 1:
            self.current_led += 1
        else:
            self.current_led = 0
        #for led in self.ledList: 
        #    led.update()

    def set_button_led(self, name, value):
        if name == "record":
            self.ledRecord.set_brightness(value)
        elif name == "next":
            self.ledNext.set_brightness(value)
        elif name == "source":
            self.ledSource.set_brightness(value)
        elif name == "freeze":
            self.ledFreeze.set_brightness(value)
        elif name == "reset":
            self.ledReset.set_brightness(value)
            #if value > 0.5:
            #    self.ledReset.set(1)
            #else:
            #    self.ledReset.set(0)
        else:
            pass

    def set_rgb(self, name, r, g, b, bright):
        col = Color(r, g, b)
        if name == "pitch_pos":
            self.ledPitchPos.set_color(col)
            self.ledPitchPos.set_brightness(bright)
        elif name == "pitch_neg":
            self.ledPitchNeg.set_color(col)
            self.ledPitchNeg.set_brightness(bright)
        elif name == "speed_pos":
            self.ledSpeedPos.set_color(col)
            self.ledSpeedPos.set_brightness(bright)
        elif name == "speed_neg":
            self.ledSpeedNeg.set_color(col)
            self.ledSpeedNeg.set_brightness(bright)
        else:
            pass

    def cleanup(self):
        self.ledReset.cleanup()

