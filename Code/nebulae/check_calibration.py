#!/bin/python2
import os
from subprocess import Popen
import switch
import calibration_collector
import sys
import time
import leddriver
import neb_globals
# import threading
# from multiprocessing import Process

class CalibrationState(object):
    __slots__ = []
    AWAITING_1V = 0
    AWAITING_3V = 1
    DONE = 2
    EXIT = 3

class CalibrationUi(object):
    """Basic class containing a frame counter, and some methods for updating the state"""

    def __init__(self):
        self.state = CalibrationState.AWAITING_1V
        self.speed_prev = False
        self.pitch_prev = False
        self.leds = leddriver.LedDriver()
        self.ignore_first_speed = True
        self.transition_hooks = {}
        self.state_change_time = time.time()

    def set_hook(self, state, callback):
        """registers a callback for a specific state"""
        self.transition_hooks[state] = callback

    def change_state(self, new_state):
        if new_state in self.transition_hooks:
            self.transition_hooks[new_state]()
        self.state = new_state
        self.state_change_time = time.time()

    def inc_state(self):
        if self.state == CalibrationState.AWAITING_1V:
            self.change_state(CalibrationState.AWAITING_3V)
        elif self.state == CalibrationState.AWAITING_3V:
            self.change_state(CalibrationState.DONE)
        elif self.state == CalibrationState.DONE:
            self.change_state(CalibrationState.EXIT)

    def tick(self):
        # update LEDs
        purple = leddriver.Color(511, 0, 4095)
        green = leddriver.Color(0, 4095, 0)

        now = time.time()
        # Initialize start_time on the first call
        if not hasattr(self, 'start_time'):
            self.start_time = now

        # Automatically move to exit state 1s after completion of calibration
        if (now - self.state_change_time) > 1.0 and self.state == CalibrationState.DONE:
            self.change_state(CalibrationState.EXIT)

        # Calculate elapsed time and use a 1-second (30 tick) period
        elapsed = now - self.start_time
        pos = (elapsed % 1.0)  # cycle duration is 1 second
        blink = 1.0 if pos > 0.5 else 0.0


        self.leds.set_rgb("speed_neg", purple.red(), purple.green(), purple.blue(), pos)
        self.leds.set_rgb("speed_pos", purple.red(), purple.green(), purple.blue(), 1.0 - pos)
        if self.state == CalibrationState.AWAITING_1V:
            self.leds.set_rgb("pitch_neg", purple.red(), purple.green(), purple.blue(), blink)
            self.leds.set_rgb("pitch_pos", purple.red(), purple.green(), purple.blue(), 0.0)
        elif self.state == CalibrationState.AWAITING_3V:
            self.leds.set_rgb("pitch_neg", green.red(), green.green(), green.blue(), 1.0)
            self.leds.set_rgb("pitch_pos", purple.red(), purple.green(), purple.blue(), blink)
        elif self.state == CalibrationState.DONE:
            self.leds.set_rgb("pitch_neg", green.red(), green.green(), green.blue(), 1.0)
            self.leds.set_rgb("pitch_pos", green.red(), green.green(), green.blue(), 1.0)
        self.leds.update()



def launch_bootled():
    cmd = "sudo pkill -1 -f /home/alarm/QB_Nebulae_V2/Code/nebulae/bootleds.py"
    os.system(cmd)
    print "Launching LED program"
    fullCmd = "python2 /home/alarm/QB_Nebulae_V2/Code/nebulae/bootleds.py calibration"
    led_process = Popen(fullCmd, shell=True)
    print 'led process created: ' + str(led_process)

def kill_bootled():
    cmd = "sudo pkill -1 -f /home/alarm/QB_Nebulae_V2/Code/nebulae/bootleds.py"
    os.system(cmd)

led_process = None

if len(sys.argv) > 1:
    arg = sys.argv[1]
else:
    arg = None
collector = calibration_collector.CalibrationCollector()
pitch_click = switch.Switch(22) # Pitch Encoder Click GPIO
pitch_click.update()
speed_click = switch.Switch(26) # Speed Encoder Click GPIO
speed_click.update()
if pitch_click.state() == True or arg == 'force':
    launch_bootled()
    #time.sleep(2)
    print 'Calibration commencing'
    collector.collect()
    # Clear out settings and factory reset
    if neb_globals.remount_fs is True:
        os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh rw")
    cmd = "rm /home/alarm/QB_Nebulae_V2/Code/config/bootinstr.txt"
    os.system(cmd)
    cmd = "rm /home/alarm/QB_Nebulae_V2/Code/config/nebsettings.txt"
    os.system(cmd)
    cmd = "rm /home/alarm/QB_Nebulae_V2/Code/config/buffer_cnt.txt"
    os.system(cmd)
    if neb_globals.remount_fs is True:
        os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh ro")
elif speed_click.state() == True or arg == 'force-voct':
    print '1V/Oct Manual Calibration Starting...'
    ui = CalibrationUi()
    now = time.time()
    last_run = now
    done_running = False
    ui.set_hook(CalibrationState.AWAITING_3V, lambda: collector.collect_v1_voct())
    ui.set_hook(CalibrationState.DONE, lambda: collector.collect_v3_voct_and_store())

    period = 0.016 # 60Hz
    next_run = time.time()
    while not done_running:
        speed_click.update()
        pitch_click.update()
        if speed_click.risingEdge():
            ui.change_state(CalibrationState.EXIT)
        if pitch_click.risingEdge():
            ui.inc_state()
        if ui.state == CalibrationState.EXIT:
            done_running = True
        if time.time() > next_run:
            ui.tick()
            next_run += period
    print '1V/Oct Manual Calibration Complete!'
else:
    print 'Skipping Calibration'
kill_bootled()

