# When running on ARM add -lwriginPi to ld and remove -fPIC from cflags
# When running on Linux remove -lwiringPi and add -fPIC

CFLAGS="-std=c99 -DPD -O3 -Wall -W -Wshadow -Wstrict-prototypes -Wno-unused -Wno-parentheses -Wno-switch -DMUUG_INTERPOLATE=1 -DMUUG_TILDE_TABLE_SIZE=512"

UNIVERSAL=-"arch x86_64 -arch i386"
DARWINCFLAGS="${CFLAGS}-DDARWIN ${UNIVERSAL} -pedantic"
DARWIN_LIBS=$UNIVERSAL

echo "osx_dummiesing externals ... -------------------------------------------------------"
echo ""

mkdir -p osx_dummies/

echo " > src/nebulae_control_adc"
cc $DARWINCFLAGS -o src/nebulae_control_adc.o -c src/nebulae_control_adc.c
cc -bundle -undefined suppress -flat_namespace $DARWIN_LIBS -o osx_dummies/nebulae_control_adc.pd_darwin src/nebulae_control_adc.o
mv src/nebulae_control_adc.pd_linux osx_dummies/

echo " > src/nebulae_input"
cc $DARWINCFLAGS -o src/nebulae_input.o -c src/nebulae_input.c
cc -bundle -undefined suppress -flat_namespace $DARWIN_LIBS -o osx_dummies/nebulae_input.pd_darwin src/nebulae_input.o
mv src/nebulae_input.pd_linux osx_dummies/

echo " > src/nebulae_output"
cc $DARWINCFLAGS -o src/nebulae_output.o -c src/nebulae_output.c
cc -bundle -undefined suppress -flat_namespace $DARWIN_LIBS -o osx_dummies/nebulae_output.pd_darwin src/nebulae_output.o
mv src/nebulae_output.pd_linux osx_dummies/

echo " > src/nebulae_encoder"
cc $DARWINCFLAGS -o src/nebulae_encoder.o -c src/nebulae_encoder.c
cc -bundle -undefined suppress -flat_namespace $DARWIN_LIBS -o osx_dummies/nebulae_encoder.pd_darwin src/nebulae_encoder.o
mv src/nebulae_encoder.pd_linux osx_dummies/

echo " > src/nebulae_shiftreg"
cc $DARWINCFLAGS -o src/nebulae_shiftreg.o -c src/nebulae_shiftreg.c
cc -bundle -undefined suppress -flat_namespace $DARWIN_LIBS -o osx_dummies/nebulae_shiftreg.pd_darwin src/nebulae_shiftreg.o
mv src/nebulae_shiftreg.pd_linux osx_dummies/

echo " > src/nebulae_leds"
cc $DARWINCFLAGS -o src/nebulae_leds.o -c src/nebulae_leds.c
cc -bundle -undefined suppress -flat_namespace $DARWIN_LIBS -o osx_dummies/nebulae_leds.pd_darwin src/nebulae_leds.o
mv src/nebulae_leds.pd_linux osx_dummies/

rm src/nebulae_control_adc.o
rm src/nebulae_input.o
rm src/nebulae_output.o
rm src/nebulae_encoder.o
rm src/nebulae_shiftreg.o
rm src/nebulae_leds.o

echo ""
