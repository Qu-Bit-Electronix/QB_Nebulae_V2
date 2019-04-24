# Create Firmware Update File for the Nebulae
# Nebulae expects a file called "neb_update.zip"
# Containing QB_Nebulae_V2/Code/*

dir="$(pwd)"
mkdir -p temp/
mkdir -p temp/QB_Nebulae_V2/
cd temp/
cp -R ../Code/ QB_Nebulae_V2/
tar -cvzf neb_update.zip QB_Nebulae_V2
cp neb_update.zip $dir
cd $dir;
rm -r temp/

