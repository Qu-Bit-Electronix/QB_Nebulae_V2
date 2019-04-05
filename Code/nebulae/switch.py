import RPi.GPIO as GPIO

class Switch(object):
    def __init__(self, pin):
        self.pin = pin
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.prev_state = 1
        self.current_state = 1

    def update(self):
        self.prev_state = self.current_state
        self.current_state = GPIO.input(self.pin)

    def risingEdge(self):
        if self.current_state == 0 and self.prev_state == 1:
            return True
        else:
            return False
    
    def fallingEdge(self):
        if self.current_state == 1 and self.prev_state == 0:
            return True
        else:
            return False

    def state(self):
        if self.current_state == 1:
            return False
        else: 
            return True

    def prevState(self):
        if self.prev_state == 1:
            return False
        else:
            return True
