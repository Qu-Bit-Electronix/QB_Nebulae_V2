# When running on ARM add -lwriginPi to ld and remove -fPIC from cflags
# When running on Linux remove -lwiringPi and add -fPIC
echo "building externals ... -------------------------------------------------------"
echo ""

mkdir -p build/

echo " > src/nebulae_control_adc"
gcc -std=c99 -O3 -Wall -c src/nebulae_control_adc.c -o src/nebulae_control_adc.o
ld --export-dynamic -shared -o src/nebulae_control_adc.pd_linux src/nebulae_control_adc.o  -lc -lm -lwiringPi
mv src/nebulae_control_adc.pd_linux build/

#echo " > src/nebulae_input"
#gcc -std=c99 -O3 -Wall -c src/nebulae_input.c -o src/nebulae_input.o
#ld --export-dynamic -shared -o src/nebulae_input.pd_linux src/nebulae_input.o  -lc -lm -lwiringPi
#mv src/nebulae_input.pd_linux build/

#echo " > src/nebulae_output"
#gcc -std=c99 -O3 -Wall -c src/nebulae_output.c -o src/nebulae_output.o
#ld --export-dynamic -shared -o src/nebulae_output.pd_linux src/nebulae_output.o  -lc -lm -lwiringPi
#mv src/nebulae_output.pd_linux build/

#echo " > src/nebulae_encoder"
#gcc -std=c99 -O3 -Wall -c src/nebulae_encoder.c -o src/nebulae_encoder.o
#ld --export-dynamic -shared -o src/nebulae_encoder.pd_linux src/nebulae_encoder.o  -lc -lm -lwiringPi
#mv src/nebulae_encoder.pd_linux build/

echo " > src/nebulae_shiftreg"
gcc -std=c99 -O3 -Wall -c src/nebulae_shiftreg.c -o src/nebulae_shiftreg.o
ld --export-dynamic -shared -o src/nebulae_shiftreg.pd_linux src/nebulae_shiftreg.o  -lc -lm -lwiringPi
mv src/nebulae_shiftreg.pd_linux build/

#echo " > src/nebulae_leds"
#gcc -std=c99 -O3 -Wall -c src/nebulae_leds.c -o src/nebulae_leds.o
#ld --export-dynamic -shared -o src/nebulae_leds.pd_linux src/nebulae_leds.o  -lc -lm -lwiringPi -lpthread
#mv src/nebulae_leds.pd_linux build/

rm src/nebulae_control_adc.o
rm src/nebulae_input.o
rm src/nebulae_output.o
rm src/nebulae_encoder.o
rm src/nebulae_shiftreg.o
rm src/nebulae_leds.o

echo ""
