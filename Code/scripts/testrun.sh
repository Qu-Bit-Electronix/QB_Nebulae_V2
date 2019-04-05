#!bin/bash
# Set the Filesystem to READ WRITE temporarily
sh /home/pi/QB_Nebulae_V2/Code/scripts/mountfs.sh rw
# Create Audio folder if it's not there (we'll make this a little more detailed later.
echo "creating home/pi/audio"
mkdir -p /home/pi/audio
echo "creating home/pi/instr"
mkdir -p /home/pi/instr
# Clear the contents of audio
echo "clearing contents of home/pi/audio"
rm -rf /home/pi/audio/*
echo "clearing contents of home/pi/instr"
rm -rf /home/pi/instr/*
# Mount USB flash device to the following location
echo "mounting usb memory"
sudo mount /dev/sda1 /mnt/memory
# Copy contents to local directory
echo "copying contents of usb memory to home/pi/audio"
cp /mnt/memory/*.wav /home/pi/audio/
cp /mnt/memory/*.aif /home/pi/audio/
cp /mnt/memory/*.aiff /home/pi/audio/
#add more, and maybe try to figure out how to wild card that bit.
echo "copying contents of usb memory to home/pi/instr"
cp /mnt/memory/*.instr /home/pi/instr/
# Set filesystem back to READ ONLY
sh /home/pi/QB_Nebulae_V2/Code/scripts/mountfs.sh ro
# Run Optimization script (I don't know if this needs to run every time or only the first time.)
echo "optimizing system."
sh /home/pi/QB_Nebulae_V2/Code/scripts/sys_opt.sh
# Verify Inputs are enabled
sh /home/pi/QB_Nebulae_V2/Code/scripts/enable_inputs.sh
# Run Main Nebulae Script Later we'll run a more detailed bootloader script that
#   will let us select instr/alternate firmware/updates/etc.
echo "starting nebulae."
python /home/pi/QB_Nebulae_V2/Code/nebulae/nebulae.py 
# Unmount folder
echo "unmounting usb memory"
sudo umount /dev/sda1

exit 
