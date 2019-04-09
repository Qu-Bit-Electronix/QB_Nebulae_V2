#!/bin/bash/
DEVICE="temp"
until [ $DEVICE = "/dev/sda1" ]
do
echo "detecting. . ."
DEVICE=$(find /dev/ | grep sda1)
sleep 2
done
echo "usb device detected."
sh /home/pi/QB_Nebulae_V2/Code/scripts/startup.sh &
exit
