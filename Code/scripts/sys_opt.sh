#!/bin/bash

# Exporting LIB path for nebulae
echo export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
# Probing i2c dev to enable i2c
sudo modprobe i2c-dev
# Stop the ntp service
sudo service ntp stop

## Stop the triggerhappy service
sudo service triggerhappy stop

## Stop the dbus service. Warning: this can cause unpredictable behaviour when running a desktop environment on the RPi
sudo service dbus stop

## Stop the console-kit-daemon service. Warning: this can cause unpredictable behaviour when running a desktop environment on the RPi
sudo killall console-kit-daemon

## Stop the polkitd service. Warning: this can cause unpredictable behaviour when running a desktop environment on the RPi
sudo killall polkitd

## Only needed when Jack2 is compiled with D-Bus support (Jack2 in the AutoStatic RPi audio repo is compiled without D-Bus support)
#export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket

## Disable Overcommit protection to allow subprocess forking when < half RAM is available.
## This may cause hardfaults if more memory than is available is actually committed.
echo 1 | sudo tee /proc/sys/vm/overcommit_memory

## Remount /dev/shm to prevent memory allocation errors
sudo mount -o remount,size=128M /dev/shm

## Kill the usespace gnome virtual filesystem daemon. Warning: this can cause unpredictable behaviour when running a desktop environment on the RPi
killall gvfsd

## Kill the userspace D-Bus daemon. Warning: this can cause unpredictable behaviour when running a desktop environment on the RPi
killall dbus-daemon

## Kill the userspace dbus-launch daemon. Warning: this can cause unpredictable behaviour when running a desktop environment on the RPi
killall dbus-launch

#disable hdmi
/opt/vc/bin/tvservice -o
#enable tvservice with:
#/opt/vc/bin/tvservice -p

## Uncomment if you'd like to disable the network adapter completely
#echo -n “1-1.1:1.0” | sudo tee /sys/bus/usb/drivers/smsc95xx/unbind
## In case the above line doesn't work try the following
#echo -n “1-1.1” | sudo tee /sys/bus/usb/drivers/usb/unbind

## Set the CPU scaling governor to performance
echo -n performance | sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
echo -n performance | sudo tee /sys/devices/system/cpu/cpu1/cpufreq/scaling_governor
echo -n performance | sudo tee /sys/devices/system/cpu/cpu2/cpufreq/scaling_governor
echo -n performance | sudo tee /sys/devices/system/cpu/cpu3/cpufreq/scaling_governor

## And finally start JACK
#jackd -P70 -p16 -t2000 -d alsa -dhw:UA25 -p 128 -n 3 -r 44100 -s &

exit
