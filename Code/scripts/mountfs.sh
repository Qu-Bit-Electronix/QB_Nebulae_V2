#!/bin/bash

case "${1}" in
    rw)
        sudo mount -o remount,rw /
        echo "Filesystem mounted in READ-WRITE mode"
        ;;
    ro)
        sudo mount -o remount,ro /
        echo "Filesystem mounted in READ-ONLY mode"
        ;;
    *)
        if [ -n "$(mount | grep mmcblk0p2 | grep -o 'rw')" ]
        then
            echo "Filesystem is mounted in READ-WRITE mode"
        else
            echo "Filesystem is mounted in READ-ONLY mode"
        fi
        echo "Usage ${0} [rw|ro]"
        ;;
    esac
exit 0
