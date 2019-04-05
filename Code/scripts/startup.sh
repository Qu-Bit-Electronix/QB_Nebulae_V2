#!/bin/bash

#sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh rw

echo "starting bootup LEDs"
python2 /home/alarm/QB_Nebulae_V2/Code/nebulae/bootleds.py booting &

echo "optimizing system."
sh /home/alarm/QB_Nebulae_V2/Code/scripts/sys_opt.sh

echo "checking for firmware update"
sh /home/alarm/QB_Nebulae_V2/Code/scripts/update.sh

#echo "checking for reversion file"
#if [ -f /mnt/memory/revert_to_factory_firmware ]
#then
#    sh /home/alarm/revertfactoryfw.sh
#fi
# Update Local Files - Config.txt (nebulae.service handled in update.)
if [ -f /home/alarm/QB_Nebulae_V2/Code/localfiles/config.txt ]
then
    echo "updating /boot/config.txt for next boot up."
    sudo bash -c "cat /home/alarm/QB_Nebulae_V2/Code/localfiles/config.txt > /boot/config.txt"
fi
#sh /home/alarm/QB_Nebulae_V2/Code/scripts/handleuserfiles.sh


# Configure Audio Codec
sh /home/alarm/QB_Nebulae_V2/Code/scripts/enable_inputs.sh


sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh rw
sudo python2 /home/alarm/QB_Nebulae_V2/Code/nebulae/check_calibration.py
sh /home/alarm/QB_Nebulae_V2/Code/scripts/mountfs.sh ro

sudo pkill -1 -f /home/alarm/QB_Nebulae_V2/Code/nebulae/bootleds.py

echo "Running Nebulae"
python2 /home/alarm/QB_Nebulae_V2/Code/nebulae/nebulae.py

exit 
