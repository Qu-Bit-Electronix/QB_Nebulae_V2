/***********************************************************************
 * terminal nebulae: GPIO
 * outputs: 
 * pcm5102a version: GPIO 16, 26 
 * wm8731   version: GPIO 12, 16
 * ****************************************************************************/

/* shensley: starting from nebulae_output.c
 * TODO:
 * - update to only use the one output.
 */


#include "m_pd.h"
#include <stdio.h>
#ifdef __arm__
	#include <wiringPi.h>
#endif

t_class *nebulae_output_class;

typedef struct _nebulae_output
{
	t_object x_obj;
	t_int clkState;
	t_int pinNum;

} t_nebulae_output;

void nebulae_output_gate(t_nebulae_output *x, t_floatarg _gate)
{
	if (_gate > 0)	x->clkState = 1; 
	else		x->clkState = 0;
	#ifdef __arm__
		digitalWrite(x->pinNum, x->clkState);
	#endif
}

void *nebulae_output_new(t_floatarg _pin)
{
	t_nebulae_output *x = (t_nebulae_output *)pd_new(nebulae_output_class);

	// valid pin?
	if (_pin == 16) x->pinNum = _pin;
	else x->pinNum = 16; // default to pin #16
	#ifdef __arm__
		pinMode(x->pinNum, OUTPUT);
	#endif
	x->clkState = 0;
	return (void *)x;
}



void nebulae_output_setup()
{
	#ifdef __arm__
		wiringPiSetupGpio();
	#endif	
	nebulae_output_class = class_new(gensym("nebulae_output"),
		(t_newmethod)nebulae_output_new,
		0, sizeof(t_nebulae_output), 
		CLASS_DEFAULT, 
		A_DEFFLOAT,
		0);
	class_addfloat(nebulae_output_class, (t_method)nebulae_output_gate);
}

