#!/bin/bash
echo ""
echo "erasing existing nebulae_* externals"
sudo rm /usr/lib/pd/extra/nebulae_*
echo "moving contents of build/ to externals"
sudo cp build/* /usr/lib/pd/extra/
echo "Done"
echo ""
