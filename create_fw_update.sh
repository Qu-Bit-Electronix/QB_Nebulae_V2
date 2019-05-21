################################################
# Create Firmware Update File for the Nebulae
#
# Nebulae expects a file called "neb_update.zip"
#
# Using the .zip extension was an oversight,
#    but the check_firmware.sh  on the Nebulae
#    is not user-updateable
################################################

echo "Creating Nebulae Firmware Update"
# Get Current Location
dir="$(pwd)"
# Create Temp Locations
mkdir -p temp/
# Move to Temp Location
cd temp/
# Copy Code/ contents to new directory structure
mkdir -p QB_Nebulae_V2/
cp -R ../Code/ QB_Nebulae_V2/
# Go through, and strip any unwanted line endings.
SEARCHDIR=./QB_Nebulae_V2/Code
for f in $SEARCHDIR/* $SEARCHDIR/**/*
do
    if [ -d "$f" ]
    then
        for ff in $f/*
        do
            if [ -f "$f" ] 
            then 
                echo "Stripping File of carriage returns: $f"
                dos2unix $f
            fi
        done
    else
        if [ -f "$f" ] 
        then 
            echo "Stripping File of carriage returns: $f"
            dos2unix $f
        fi
    fi
done
# Create Update File
tar -czf neb_update.zip QB_Nebulae_V2
# Copy Update File to user directory
cp neb_update.zip $dir
# Return to user directory
cd $dir;
# Erase Temp Files
rm -r temp/
echo "Done."

