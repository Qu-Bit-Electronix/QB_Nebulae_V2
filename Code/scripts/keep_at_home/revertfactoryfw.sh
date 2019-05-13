#! /bin/bash
echo "Checking that revert file is there"
if [ -f /mnt/memory/revert_to_factory_firmware ]
then
    echo "Checking that backup exists"
    if [ -d /home/pi/backup/factory ]
    then
    echo "Removing Current Firmware"
    rm -rf /home/pi/QB_Nebulae_V2
    echo "Reinstalling Factory Firmware"
    cp -R /home/pi/backup/factory/QB_Nebulae_V2 /home/pi/
    fi
    sudo rm -rf /mnt/memory/revert_to_factory_firmware
else
    echo "No Reversion file present. Moving On."
fi

