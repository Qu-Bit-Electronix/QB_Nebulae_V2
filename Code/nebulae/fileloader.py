import glob
import os
from subprocess import Popen
import neb_globals
#import shutil

class FileLoader(object):
    def __init__(self):
        self.states = ["reloading", "idling"]
        self.stateFunctions = {}
        self.stateFunctions["idling"] = None
        self.stateFunctions["reloading"] = self.reload
        self.numStates = len(self.states)
        self.currentState = self.states[self.numStates-1]
        self.audiotypes = [ ".wav", ".aif", ".aiff", ".flac"]
        self.instrtypes = [".instr"]
        self.pdtypes = [".pd"]
        self.csdtypes = [".csd"]
        self.scdtypes = [".scd"]
        self.othertypes = [".c", ".sh", ".cpp", ".cc"]
        self.dirs = [ "audio", "instr", "pd", "supercollider", "csound", "other"]
        self.dirtypes = {}
        self.dirtypes["audio"] = self.audiotypes
        self.dirtypes["instr"] = self.instrtypes
        self.dirtypes["pd"] = self.pdtypes
        self.dirtypes["csd"] = self.csdtypes
        self.dirtypes["scd"] = self.scdtypes
        self.dirtypes["other"] = self.othertypes
        self.usb_mounted = self.isUSBMounted()
        self.led_process = None

    def update(self):
        if self.currentState < self.numStates:
          # do state step
          if self.currentState != "idling":
              self.stateFunctions[self.currentState]
              self.currentState += 1

    def reload(self):
        if neb_globals.remount_fs is True:
            os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh rw")
        self.mount()
        if self.usb_mounted == True:
            self.launch_bootled(1)
            self.copyType("audio")
            self.copyType("instr")
            self.copyType("pd")
            self.umount()
        else:
            self.launch_bootled(0)
        if self.led_process is not None:
            # Kill Boot LED
            self.led_process.kill()
        if neb_globals.remount_fs is True:
            os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh ro")

    def mount(self):
        print "Mounting USB Device"
        os.system("mount /dev/sda1 /mnt/memory")
        self.usb_mounted = self.isUSBMounted()

    def umount(self):
        print "Unmounting USB Device"
        os.system("umount /dev/sda1" )
        print "Sync filebuffers to disk."
        os.system("sync")
        self.usb_mounted = self.isUSBMounted()

    def isUSBMounted(self):
        try:
            with open("/proc/mounts", "r") as f:
                for line in f:
                    if "/mnt/memory" in line:
                        return True
        except:
            print "Could not check for mounted drives."

        return False

    def copyFileToUSB(self, filepath):
        if os.path.isfile(filepath):
            fileDir = '/mnt/memory'
            if neb_globals.remount_fs is True:
                os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh rw")
            self.mount()
            if self.isUSBMounted():
                cmd = "cp " + filepath + " " + fileDir
                os.system(cmd)
                self.umount()
            if neb_globals.remount_fs is True:
                os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh ro")

    def copyType(self, fileType):
        fileDir = '/mnt/memory'
        files = []
        for ext in self.dirtypes[fileType]:
            files.extend(glob.glob(fileDir + '/*' + ext))
        fileCount = len(files)
        if fileCount > 0:
            fullDir = "/home/alarm/" + fileType
            cmd = "mkdir -p " + fullDir
            os.system(cmd)
            #fullFile = fullDir + "/*" + ext
            print "Erasing " + fullDir
            cmd = "rm " + fullDir + "/*"
            os.system(cmd)
            print "Contents of " + fullDir + " after erasure:"
            cmd = "ls " + fullDir
            os.system(cmd)
            for f in files:
                #new_f = f.replace(" ", "\ ").replace("\'", "\\\'")
                new_f = '"{0}"'.format(f)
                s = " ".join(["cp", new_f,fullDir])
                os.system(s)
                # shutil implementation
                #fstr = "*"+ ext
                #sstr = "/mnt/memory/"+fstr
                #dstr = fullDir+fstr
                #shutil.copy(sstr, dstr)


    def getState(self):
        return self.currentState

    def launch_bootled(self, mode):
        cmd = "sudo pkill -1 -f /home/alarm/QB_Nebulae_V2/Code/nebulae/bootleds.py"
        os.system(cmd)
        print "Launching LED program"
        if mode == 0:
            fullCmd = "python2 /home/alarm/QB_Nebulae_V2/Code/nebulae/bootleds.py loading"
        else:
            fullCmd = "python2 /home/alarm/QB_Nebulae_V2/Code/nebulae/bootleds.py loadingusb"
        self.led_process = Popen(fullCmd, shell=True)
        print 'led process created: ' + str(self.led_process)
