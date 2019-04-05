/* NB: pullups need to be set for the inputs to work */
/* shensley: started with tedium_input.c - thanks! */

/* TODO:
 * - test with the correct pin numbers just to verify, but then:
 * - convert pin number argument to be a string argument, "reset", "record", etc.
 * - not sure if this just bangs or is a state output. it should probably be state relative.
 */

#include "m_pd.h"
#include <stdio.h>
#ifdef __arm__
	#include <wiringPi.h>
#endif

t_class *nebulae_input_class;

typedef struct _nebulae_input
{
	t_object x_obj;
	t_clock *x_clock;
	t_int clkState;
	t_int pinNum;
	t_outlet *x_out;

} t_nebulae_input;

void nebulae_input_tick(t_nebulae_input *x)
{
	int prevState = x->clkState;
	#ifdef __arm__
		x->clkState = digitalRead(x->pinNum); 
	#endif
	// pin pulled low since last tick ?
	if(prevState && !x->clkState) outlet_bang(x->x_out);
	clock_delay(x->x_clock, 0x1); 
}

void *nebulae_input_new(t_floatarg _pin)
{
	t_nebulae_input *x = (t_nebulae_input *)pd_new(nebulae_input_class);
	x->x_clock = clock_new(x, (t_method)nebulae_input_tick);
	// valid pin?
	//if (_pin == 4 || _pin == 17 || _pin == 2 || _pin == 3 || _pin == 14 || _pin == 27 || _pin == 23 || _pin == 24 || _pin == 25) x->pinNum = _pin;
    if (_pin == 4 || _pin == 23 || _pin == 24 || _pin == 25) x->pinNum = _pin;
	else x->pinNum = 4; // default to pin #4	
	#ifdef __arm__
		pinMode(x->pinNum, INPUT);
		pullUpDnControl(x->pinNum, PUD_UP);
	#endif
	x->x_out = outlet_new(&x->x_obj, gensym("bang"));
	nebulae_input_tick(x);
	return (void *)x;
}

void nebulae_input_free(t_nebulae_input *x)
{
	clock_free(x->x_clock);
	outlet_free(x->x_out);  
}

void nebulae_input_setup()
{
	#ifdef __arm__
		wiringPiSetupGpio();
	#endif	
	nebulae_input_class = class_new(gensym("nebulae_input"),
		(t_newmethod)nebulae_input_new, (t_method)nebulae_input_free,
		sizeof(t_nebulae_input), 
		CLASS_NOINLET, 
		A_DEFFLOAT,
		0);
}

