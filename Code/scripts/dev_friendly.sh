#!/bin/sh
# This script reenables internet access, syncs the time, and leaves the disk in
# read/write mode.
# It also disables the nebulae service.
# This will need to be run as root, or with sudo

LOC=/home/alarm/QB_Nebulae_V2/Code/scripts/

$LOC/mountfs.sh rw
sudo systemctl unmask systemd-resolved
sudo systemctl enable systemd-resolved
sudo systemctl restart systemd-resolved
sudo timedatectl set-ntp true
sudo systemctl restart systemd-timesyncd
sudo systemctl stop nebulae
