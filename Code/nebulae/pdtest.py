import controlhandler
import ui
from subprocess import Popen
import sys
import os
patch = "rhythmic_chords_tcp"
fullPath = "/home/alarm/QB_Nebulae_V2/Code/pd/" + patch + ".pd"
cmd = "pd -nogui -verbose -rt -audiobuf 5".split()
cmd.append(fullPath)
pt = Popen(cmd)
request = False
ch = controlhandler.ControlHandler(None, 0, None)
ch.enterPureDataMode()
ui = ui.UserInterface(ch)
while(request != True):
    ch.updateAll()
    ui.update()
