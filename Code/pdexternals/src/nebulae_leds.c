/***********************************************************************
 # Nebulae - LEDS external
 # 17 inlets to control brightness of each LED on the nebulae.
 # grouped as listed below:
 # - speed neg r, g, b
 # - speed pos r, g, b
 # - pitch neg r, g, b
 # - pitch pos r, g, b
 # - buttons record, next, source, reset, freeze
 # 
 # - All, but one LED is driven from a PCA9685, the reset LED will be configured for software PWM.
 # - All inputs will either be 0-4095 or 0-1 (I'll decide soon.)
 * ****************************************************************************/

#include "m_pd.h"
#include <unistd.h>
#include <stdint.h>
#include <stdio.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#ifdef __arm__
	/* TODO: Rebuild driver to use kernal drivers instead of WiringPI
    #include <sys/ioctl.h>
    #include <fcntl.h>
    #include <linux/x/xdev.h>
	*/
    #include <wiringPi.h>
    #include <softPwm.h>
	#include <wiringPiI2C.h>
	#define DEVICE 0x40
	#define MODE1 0x00 // location for Mode1 register address
	#define MODE2 0x01 // location for Mode2 reigster address
	#define PRE_SCALE_MODE 0xFE //location for setting prescale (clock speed)
    #define LED0_ON_L 0x06
    #define LED0_ON_H 0x07
    #define LED0_OFF_L 0x08
    #define LED0_OFF_H 0x09
    // Bits:
    #define RESTART 0x80
    #define SLEEP 0x10
    #define ALLCALL 0x01
    #define INVRT 0x10
    #define OUTDRV 0x04
    // Reset:
    #define PWM_PIN 12
#endif

static t_class *nebulae_leds_class;

typedef struct _nebulae_leds
{
    t_object x_obj;
	t_inlet *x_in_bright[17];
    int _version;
    int fd;
    float data_pca[16];
    float data_reset;
} t_nebulae_leds;

static t_nebulae_leds *nebulae_leds_new(t_floatarg version);
static void nebulae_leds_free(t_nebulae_leds *x);
static void nebulae_leds_bang(t_nebulae_leds *x);
static void nebulae_leds_reset(t_nebulae_leds *x);

static void nebulae_leds_bang(t_nebulae_leds *x)
{
	// Update all LEDs
	#ifdef __arm__
	unsigned int data;
    unsigned char trunc[2];
    for (unsigned int i = 0; i < 16; i++) {
        data = (unsigned int)(round(x->data_pca[i] * 4095.0));
        trunc[0] = data & 0xFF;
        trunc[1] = (data >> 8) & 0xFF;
        wiringPiI2CWriteReg8(x->fd, LED0_ON_L+(4*i), 0);
        wiringPiI2CWriteReg8(x->fd, LED0_ON_H+(4*i), 0);
        wiringPiI2CWriteReg8(x->fd, LED0_OFF_L+(4*i), trunc[0]);
        wiringPiI2CWriteReg8(x->fd, LED0_OFF_H+(4*i), trunc[1]);
    }
    data = (unsigned int)round(x->data_reset * 100.0);
    softPwmWrite(PWM_PIN, data);
	#endif
}
/********************************************************************
 * This function frees the object (destructor).
 * ******************************************************************/
static void nebulae_leds_free(t_nebulae_leds *x){
		// free i2c.
		for (unsigned int i = 0; i < 17; i++) {
			inlet_free(x->x_in_bright[i]);
		}
}

/*************************************************
 * init function.
 * ***********************************************/
static t_nebulae_leds *nebulae_leds_new(t_floatarg version){
    t_nebulae_leds *x = (t_nebulae_leds *)pd_new(nebulae_leds_class);
    for (unsigned int i = 0; i < 16; i++) {
				x->x_in_bright[i] = floatinlet_new(&x->x_obj, &x->data_pca[i]); // if my pointer instincts are off.
    }
    x->x_in_bright[16] = floatinlet_new(&x->x_obj, &x->data_reset);
    #ifdef __arm__
        x->fd = wiringPiI2CSetup(DEVICE);
        softPwmCreate(PWM_PIN, 0, 100);
        printf ("Init Result: %d\n", x->fd);
    #endif
    return(x);
}

static void nebulae_leds_open(t_nebulae_leds *x){
    nebulae_leds_reset(x);
    
}

static void nebulae_leds_reset(t_nebulae_leds *x)
{
	#ifdef __arm__
    if (x->fd >= 0) {
        unsigned char mode; 
        wiringPiI2CWriteReg8(x->fd, MODE2, OUTDRV);
        wiringPiI2CWriteReg8(x->fd, MODE1, ALLCALL);
        delay(10);
        mode = wiringPiI2CReadReg8(x->fd, MODE1);
        mode = mode & ~SLEEP;
        wiringPiI2CWriteReg8(x->fd, MODE1, mode);
        delay(10);
        wiringPiI2CReadReg8(x->fd, MODE1);
        delay(10);
    }
    // Setup Reset LED as software PWM.
	#endif	

}


void nebulae_leds_setup(void)
{
   
	#ifdef __arm__
		wiringPiSetupGpio();
	#endif	
    nebulae_leds_class = class_new(gensym("nebulae_leds"), (t_newmethod)nebulae_leds_new,
        (t_method)nebulae_leds_free, sizeof(t_nebulae_leds), 0, A_DEFSYM, 0);
    class_addmethod(nebulae_leds_class, (t_method)nebulae_leds_open, gensym("open"), 
        A_DEFSYM, 0);
    class_addbang(nebulae_leds_class, nebulae_leds_bang);
}

