#!/bin/bash
case "${1}" in
    enable)
        sudo systemctl unmask systemd-resolved.service
        sudo systemctl enable systemd-resolved.service
        sudo systemctl restart systemd-resolved.service
        echo "systemd-resolved.service is enabled"
        ;;
    disable)
        sudo mount -o remount,ro /
        sudo systemctl mask systemd-resolved.service
        sudo systemctl stop systemd-resolved.service
        sudo systemctl restart systemd-resolved.service
        echo "systemd-resolved.service is disabled"
        ;;
    *)
        echo "Usage ${0} [enable|disable]"
        ;;
    esac
exit 0
