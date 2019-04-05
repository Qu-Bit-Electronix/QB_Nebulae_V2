import os
import time
import controlhandler

class CalibrationCollector(object):
    def __init__(self):
        self.ch = controlhandler.ControlHandler(None, 0, None) # Create new Controlhandler.

    def collect(self):
        self.ch.updateAll()
        #data = []
        avg = 0
        numSamps = 4096
        names = ['start', 'size', 'density', 'overlap', 'blend', 'window', 'speed', 'pitch']
        avgs = {}
        for name in names:
            avgs[name] = 0.0
        for i in range(0, numSamps):
            self.ch.updateAll()
            for name in names:
                val = self.ch.channeldict[name].getRawCVValue()
                avgs[name] += val
        for name in names:
            avgs[name] = avgs[name] / numSamps
        filepath = '/home/alarm/QB_Nebulae_V2/Code/misc/'
        filename = 'calibration_data.txt'
        os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh rw")
        with open(filepath + filename, 'w') as myfile:
            for name in names:
                stuff = [name, str(avgs[name]), '\n']
                line = ','.join(stuff)
                myfile.write(line)
        os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh ro")
            

