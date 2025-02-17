import os
import time
import controlhandler


class CalibrationCollector(object):
    def __init__(self):
        self.ch = controlhandler.ControlHandler(
            None, 0, None
        )  # Create new Controlhandler.

        self.v1 = 0
        self.v3 = 0

    def collect(self):
        self.ch.updateAll()
        # data = []
        avg = 0
        numSamps = 4096
        names = [
            "start",
            "size",
            "density",
            "overlap",
            "blend",
            "window",
            "speed",
            "pitch",
        ]
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
        filepath = "/home/alarm/QB_Nebulae_V2/Code/misc/"
        filename = "calibration_data.txt"
        os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh rw")
        with open(filepath + filename, "w") as myfile:
            for name in names:
                stuff = [name, str(avgs[name]), "\n"]
                line = ",".join(stuff)
                myfile.write(line)
        os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh ro")

    def collect_v1_voct(self):
        self.ch.updateAll()
        self.v1 = self.ch.channeldict["pitch"].getRawCVValue()

    def collect_v3_voct_and_store(self):
        self.ch.updateAll()
        self.v3 = self.ch.channeldict["pitch"].getRawCVValue()
        delta = self.v3 - self.v1
        if delta == 0.0:
            return
        scale = 24.0 / delta
        offset = 12 - scale * self.v1
        os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh rw")
        filepath = "/home/alarm/QB_Nebulae_V2/Code/misc/"
        filename = "calibration_data.txt"
        with open(filepath + filename, "w") as myfile:
            l1 = ",".join(["pitch_voct_scale", scale, "\n"])
            l2 = ",".join(["pitch_voct_offset", offset, "\n"])
            myfile.write(l1)
            myfile.write(l2)
        os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh ro")
