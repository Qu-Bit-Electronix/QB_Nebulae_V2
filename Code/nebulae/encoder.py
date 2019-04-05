# encoder.py
# Stephen Hensley
# Encoder Class Adapted from py-gaugette rotary encoder library

import RPi.GPIO as GPIO
import time
import math
import threading

class Encoder:

    def __init__(self, pin_a, pin_b):
        self.pin_a = pin_b; # Our Encoders are inverted,
        self.pin_b = pin_a; # Which is why this looks weird
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.pin_a, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.pin_b, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.steps = 0
        self.last_delta = 0
        self.r_seq = self.rotation_sequence()
        self.steps_per_cycle = 4
        self.remainder = 0

    def rotation_state(self):
        a_state = GPIO.input(self.pin_a)
        b_state = GPIO.input(self.pin_b)
        r_state = a_state | b_state << 1
        return r_state

    def rotation_sequence(self):
        a_state = GPIO.input(self.pin_a)
        b_state = GPIO.input(self.pin_b)
        r_seq = (a_state ^ b_state) | b_state << 1
        return r_seq

    def update(self):
        delta = 0
        r_seq = self.rotation_sequence()
        if (r_seq != self.r_seq):
            delta = (r_seq - self.r_seq) % 4
            if delta == 3:
                delta = -1
            elif delta == 2:
                delta = int(math.copysign(delta, self.last_delta))
            self.last_delta = delta
            self.r_seq = r_seq
        self.steps += delta

    def get_steps(self):
        steps = self.steps
        self.steps = 0
        return steps

    def get_cycles(self):
        self.remainder += self.get_steps()
        cycles = self.remainder // self.steps_per_cycle
        self.remainder %= self.steps_per_cycle
        return cycles

    def start(self):
        def isr():
            self.update()
        GPIO.add_event_detect(self.pin_a, GPIO.BOTH, isr)
        GPIO.add_event_detect(self.pin_b, GPIO.BOTH, isr)

    class Worker(threading.Thread):
        def __init__(self, pin_a, pin_b):
            threading.Thread.__init__(self)
            self.lock = threading.Lock()
            self.stopping = False
            self.encoder = Encoder(pin_a, pin_b)
            self.daemon = True
            self.delta = 0
            self.delay = 0.001

        def run(self):
            while not self.stopping:
                self.encoder.update()
                time.sleep(self.delay)

        def stop(self):
            self.stopping = True

        def get_steps(self):
            return self.encoder.get_steps()
