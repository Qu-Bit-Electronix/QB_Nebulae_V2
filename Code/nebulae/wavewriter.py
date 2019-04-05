import wave
import numpy as np
import struct
import ctypes
import os
import fileloader
import neb_globals

class WaveWriter(object):
    def __init__(self):
        self.fpath = "/home/alarm/QB_Nebulae_V2/Code/config/buffer_cnt.txt"
        if os.path.isfile(self.fpath) and os.path.getsize(self.fpath) > 0:
            with open(self.fpath, 'r') as myfile:
                for line in myfile:
                    if line.strip():
                        self.num_written = int(line)
        else:
            self.num_written = 0
            if neb_globals.remount_fs is True:
                os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh rw")
            with open(self.fpath, 'w') as myfile:
                myfile.write(str(self.num_written))
            if neb_globals.remount_fs is True:
                os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh ro")
        self.outpath = "/mnt/memory/"
        self.default_name = "neb_buffer_"
        self.extension = ".wav"
        self.nchannels = 2
        self.sampwidth = 2 # for int16_t
        self.framerate = 48000
        self.usbloader = fileloader.FileLoader()

    def WriteStereoWaveFile(self, datal, datar, length):
        success = False
        self.usbloader.mount()
        if self.usbloader.isUSBMounted():
            print ("USB Mounted, proceeding")
            filename = self.outpath + self.default_name + str(self.num_written) + self.extension
            # Determine Length (Assumes both arrays are same length)
            maxamp = 32767.0
            # Interleave Data
            if length > 0:
                disk = os.statvfs("/mnt/memory")
                bytesToWrite = length * self.nchannels* self.sampwidth 
                bytesAvailable = disk.f_bsize * disk.f_bfree
                print "Calculated length: " + str(length)
                print "Bytes to write: " + str(bytesToWrite)
                print "Bytes available: " + str(bytesAvailable)
                sublength = 30 * self.framerate # 1 minute at a time
                # Write Audio File
                if bytesToWrite < bytesAvailable:
                    try:
                        print("Writing Audio File. . . ")
                        out = wave.open(filename, 'wb')
                        out.setnframes(length * self.nchannels)
                        out.setnchannels(self.nchannels)
                        out.setsampwidth(self.sampwidth)
                        out.setframerate(self.framerate)
                        idx = 0
                        while idx < length:
                            if sublength + idx < length:
                                writesize = sublength
                            else:
                                writesize = (length - idx)
                            print("Writing " + str(writesize) + " samples starting at idx: " + str(idx))
                            end = int(writesize + idx)
                            interleaved_data = np.ravel(np.column_stack((datal[idx:end] * maxamp, datar[idx:end] * maxamp))).astype('int16', copy=False).tostring()
                            idx += writesize
                            out.writeframesraw(interleaved_data)
                        out.writeframes('')
                        out.close()
                        print("Done.")
                        # Update Tracker of number of files.
                        self.num_written += 1
                        if neb_globals.remount_fs is True:
                            os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh rw")
                        with open(self.fpath, 'w') as myfile:
                            myfile.write(str(self.num_written))
                        if neb_globals.remount_fs is True:
                            os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh ro")
                        success = True
                    except:
                        print("Could not write file! -- Inspecific Exception")
                else:
                    print("Not enough room to write file.")
            else:
                print("Buffer is empty. Nothing valuable to write.")
        else:
            print("No USB Present -- not storing buffer")
        self.usbloader.umount()
        return success
        
        
