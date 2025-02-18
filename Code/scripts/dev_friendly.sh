#!/bin/sh
# This script reenables internet access, syncs the time, and leaves the disk in
# read/write mode.
# It also disables the nebulae service.
# This will need to be run as root, or with sudo

LOC=/home/alarm/QB_Nebulae_V2/Code/scripts/

$LOC/mountfs.sh rw
systemctl unmask systemd-resolved
systemctl enable systemd-resolved
systemctl restart systemd-resolved
timedatectl set-ntp true
systemctl restart systemd-timesyncd
systemctl stop nebulae
