"""Handles collecting, storage, and retrieval of calibration data for Nebulae"""

import controlhandler
from calibration_data import CalibrationData


class CalibrationCollector(object):
    """Handles recording calibration data from hardware"""

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
        # numSamps = 4096
        numSamps = 1024
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

        caldata = CalibrationData()
        for name in names:
            caldata.offsets[name] = avgs[name]
        caldata.save()

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

        caldata = CalibrationData()
        caldata.voct_scaling = scale / 60.0
        caldata.voct_offset = offset / 60.0
        caldata.manually_calibrated = True
        caldata.save()
