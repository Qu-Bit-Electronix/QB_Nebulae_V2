"""Handles collecting, storage, and retrieval of calibration data for Nebulae"""

import os
import controlhandler
import json


class CalibrationData(object):
    """
    Class storing the data for calibrating ADC inputs on Nebulae
    in addition to as logic for storing and retrieving the data from disk.

    The initializer for this struct will internally run the load method.
    This will always fill a new instance of this class with the latest data from disk.
    """

    FILEPATH = "/home/alarm/QB_Nebulae_V2/Code/misc/"
    LEGACY_FNAME = "calibration_data.txt"
    FNAME = "calibration_data.json"

    def __init__(self):
        self.offsets = {
            "start": 0.0,
            "size": 0.0,
            "density": 0.0,
            "overlap": 0.0,
            "blend": 0.0,
            "window": 0.0,
            "speed": 0.0,
            "pitch": 0.0,
        }
        self.voct_scaling = 0.8685
        self.voct_offset = 0.0
        self.manually_calibrated = False
        self.load()

    def to_dict(self):
        """Converts inner data to a dictionary"""
        return {
            "offsets": self.offsets,
            "voct_scaling": self.voct_scaling,
            "voct_offset": self.voct_offset,
            "manually_calibrated": self.manually_calibrated,
        }

    def save(self):
        """
        Save the inner data to a json file
        """
        path = self.FILEPATH + self.FNAME
        os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh rw")
        data = self.to_dict()
        with open(path, "w") as f:
            json.dump(data, f)
        os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh ro")

    def load(self):
        """
        Fills the structure with existing data

        First, this checks if the new JSON format file exists,
        if it does, that file is used to populate the data in the instance of the class.
        Otherwise, this will check for the legacy file type, and fill the data with that.
        If the legacy file is found, the data will be immediately be written to the new format,
        and the old file will be deleted.
        If neither the new, or legacy file formats exist, the default data for the structure
        will remain unchanged.

        Returns boolean for whether any data was loaded
        """
        found_new_format = self._load_from_json()
        if not found_new_format:
            found_legacy = self._load_from_legacy_file()
            if found_legacy:
                self.save()
                self._remove_legacy_file()
        return found_new_format or found_legacy

    def _from_dict(self, data):
        """Fills data from dictionary"""
        self.offsets = data["offsets"]
        self.voct_scaling = data["voct_scaling"]
        self.voct_offset = data["self.voct_offset"]
        self.manually_calibrated = data["self.manually_calibrated"]

    def _load_from_legacy_file(self):
        """
        Opens the legacy .txt file containing calibration data, and fills the inner data
        Returns false if the file does not exist.
        """
        path = self.FILEPATH + self.LEGACY_FNAME
        if not os.path.exists(path):
            return False
        os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh rw")
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
        with open(path, "r") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) == 2:
                    name, value = parts
                    if name in names:
                        self.offsets[name] = float(value)
        os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh ro")
        return True

    def _load_from_json(self):
        """
        Opens a json file containing the stored data, and fills the inner data
        Returns false if no file exists, or true if it loads
        """
        path = self.FILEPATH + self.FNAME
        if not os.path.exists(path):
            return False
        os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh rw")
        with open(path, "r") as f:
            data = json.load(f)
            # wouldn't be bad to add some validation here..
            self._from_dict(data)
        os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh ro")
        return True

    def _remove_legacy_file(self):
        """
        Removes the legacy calibration file from disk
        """
        path = self.FILEPATH + self.LEGACY_FNAME
        if os.path.exists(path):
            os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh rw")
            os.remove(path)
            os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh ro")


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
