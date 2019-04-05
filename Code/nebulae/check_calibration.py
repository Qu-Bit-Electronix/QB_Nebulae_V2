#!/bin/python2
import os
from subprocess import Popen
import switch
import calibration_collector
import sys
import time

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
else:
    print 'Skipping Calibration'
kill_bootled()


