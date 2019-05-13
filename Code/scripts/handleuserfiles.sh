#!/bin/bash
# Create User dirs if it's not there (we'll make this a little more detailed later.
#echo "creating home/alarm/audio"
#mkdir -p /home/alarm/audio
#echo "creating home/alarm/instr"
#mkdir -p /home/alarm/instr
#echo "creating home/alarm/pd"
#mkdir -p /home/alarm/pd

# Mount USB flash device to the following location
#echo "mounting usb memory"
#sudo mount /dev/sda1 /mnt/memory

# Clear the contents of user dirs
# TODO: Check to see if there are corresponding files on the USB Drive.
# If so, clear the dir.
# If not, leave files in place.
#echo "clearing contents of home/alarm/audio"
#rm -rf /home/alarm/audio/*
#echo "clearing contents of home/alarm/instr"
#rm -rf /home/alarm/instr/*
#echo "clearing contents of home/alarm/pd"
#rm -rf /home/alarm/pd/*

# Copy contents to local directory
# TODO: add more file formats
#echo "copying contents of usb memory to home/alarm/audio"
#cp /mnt/memory/*.wav /home/alarm/audio/
#cp /mnt/memory/*.aif /home/alarm/audio/
#cp /mnt/memory/*.aiff /home/alarm/audio/
#cp /mnt/memory/*.flac /home/alarm/audio/

# User Instruments
# TODO: Add supercollider, user shell scripts, and .csd playback
#echo "copying contents of usb memory to home/alarm/instr"
#cp /mnt/memory/*.instr /home/alarm/instr/
#cp /mnt/memory/*.pd /home/alarm/pd/

# Unmount folder
#echo "unmounting usb memory"
#sudo umount /dev/sda1

