import os
from time import gmtime, strftime
import neb_globals

class NebLogger(object):

    def __init__(self):
        self.usb_status = False
        self.write_local = True #requires remount
        self.write_remote = True
        self.system_data = {}
        self.acquireSystemData()
        self.localpath = "/home/alarm/QB_Nebulae_V2/Code/log/neb_log.txt"
        self.remotepath = "/mnt/memory/neb_log.txt"

    def spill_basic_info(self):
        self.check_usb_status()
        if self.write_remote == True:
            self.mount_usb()
            if self.usb_status == True:
                for key in self.system_data.iterkeys():
                    cmd_suffix = " >> /mnt/memory/neb_log.txt"
                    ts = self.getTimeStamp() + " --- "
                    item = key + ", " + self.system_data[key].rstrip()
                    cmd_remote = "echo \"" + ts + item + "\"" + cmd_suffix
                    os.system(cmd_remote)
                self.spill_cpu_data(self.remotepath)
                self.unmount_usb()
        if self.write_local == True:
            if neb_globals.remount_fs is True:
                os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh rw")
            print "Adding to Local Log"
            for key in self.system_data.iterkeys():
                cmd_suffix = " >> /home/alarm/QB_Nebulae_V2/Code/log/neb_log.txt"
                ts = self.getTimeStamp() + " --- "
                item = key + ", " + self.system_data[key].rstrip()
                cmd_local = "echo \"" + ts + item + "\"" + cmd_suffix
                os.system(cmd_local)
            self.spill_cpu_data(self.localpath)
            if neb_globals.remount_fs is True:
                os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh ro")

    def spill_cpu_data(self, path):
        # We'll log the cpu temp, and the amount of available memory 
        os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/gettemp.sh >> " + path)
        os.system("free -h >>" + path)

    def check_usb_status(self):
        self.usb_status = False
        with open("/etc/mtab", "r") as f:
            for line in f:
                if "/mnt/memory" in line:
                    self.usb_status = True

    def mount_usb(self):
        self.check_usb_status() 
        if self.usb_status == True:
            print "USB drive is already mounted"
        else:
            if neb_globals.remount_fs is True:
                os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh rw")
            print "Mounting USB Device"
            os.system("mount /dev/sda1 /mnt/memory")
            self.check_usb_status()
            if self.usb_status == True:
                print "USB drive is now mounted."
            if neb_globals.remount_fs is True:
                os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh ro")

    def unmount_usb(self):
        self.check_usb_status() 
        if self.usb_status == False:
            print "USB drive is not mounted"
        else:
            if neb_globals.remount_fs is True:
                os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh rw")
            print "Unmounting USB Device"
            os.system("umount /dev/sda1")
            self.check_usb_status()
            if self.usb_status == False:
                print "USB drive is now safe to eject."
            if neb_globals.remount_fs is True:
                os.system("sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh ro")

    def acquireSystemData(self):
        with open("/home/alarm/QB_Nebulae_V2/Code/config.txt", "r") as f:
            for line in f:
                items = line.split("=")
                if len(items) > 1:
                    self.system_data[items[0]] = items[1]
                else:
                    print "Invalid entry in config.txt:"
                    print line

    def getTimeStamp(self):
        return strftime("%a, %d %b %Y %H: %M:%S +0000", gmtime())
        
