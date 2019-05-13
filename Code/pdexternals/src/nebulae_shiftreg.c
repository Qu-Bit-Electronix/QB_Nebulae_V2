/***********************************************************************
 * nebulae: shift register
 * button inputs (and source gate)
 * - runs on own clock to not miss events.
 * - 6 outlets - record, next, source, reset, freeze, source_gate
 * ****************************************************************************/


#include "m_pd.h"
#include <stdio.h>
#ifdef __arm__
	#include <wiringPi.h>
    #include <wiringShift.h>
#endif

t_class *nebulae_shiftreg_class;

typedef struct _nebulae_shiftreg
{
	t_object x_obj;
	t_clock *x_clock;
	t_int pin_data;
    t_int pin_clk;
    t_int pin_latch;
    t_int prev_state[6];
	t_int state[6];
    t_outlet *x_out[6];

} t_nebulae_shiftreg;

void nebulae_shiftreg_tick(t_nebulae_shiftreg *x)
{
    int vals[8];
    int pos_map[6] = { 7, 6, 5, 4, 3, 0 };
    int pos;
    for (unsigned int i = 0; i < 6; i++) {
        x->prev_state[i] = x->state[i];
    }
	#ifdef __arm__
        digitalWrite(x->pin_latch, 1);
        digitalWrite(x->pin_latch, 0);
        for (unsigned int i = 0; i < 8; i++) {
            digitalWrite(x->pin_clk, 0); 
            vals[i] = digitalRead(x->pin_data);
            digitalWrite(x->pin_clk, 1);
            delay(4);
        }     
        digitalWrite(x->pin_latch, 1);
        //digitalWrite(x->pin_latch, 1);
	#endif
    for (unsigned int i = 0; i < 6; i++) {
        pos = pos_map[i]; 
        x->state[i] = vals[pos];  
        if (x->prev_state[i] != x->state[i]) {
            outlet_float(x->x_out[i], x->state[i]);
        }
    }
	clock_delay(x->x_clock, 0x1); 
}

void *nebulae_shiftreg_new(t_floatarg _pin)
{
	t_nebulae_shiftreg *x = (t_nebulae_shiftreg *)pd_new(nebulae_shiftreg_class);
	x->x_clock = clock_new(x, (t_method)nebulae_shiftreg_tick);
    x->pin_clk = 14;
    x->pin_latch = 15;
    x->pin_data = 5;
	#ifdef __arm__
		pinMode(x->pin_clk, OUTPUT);
		pinMode(x->pin_latch, OUTPUT);
		pinMode(x->pin_data, INPUT);
        pullUpDnControl(x->pin_clk, PUD_OFF);
        pullUpDnControl(x->pin_latch, PUD_OFF);
        pullUpDnControl(x->pin_data, PUD_OFF);
	#endif
    for (unsigned int i = 0; i < 6; i++) {
	    x->x_out[i] = outlet_new(&x->x_obj, gensym("float"));
    }
	nebulae_shiftreg_tick(x);
	return (void *)x;
}

void nebulae_shiftreg_free(t_nebulae_shiftreg *x)
{
	clock_free(x->x_clock);
    for (unsigned int i = 0; i < 6; i++) {
	    outlet_free(x->x_out[i]);  
    }
}


void nebulae_shiftreg_setup()
{
	#ifdef __arm__
		wiringPiSetupGpio();
	#endif	
	nebulae_shiftreg_class = class_new(gensym("nebulae_shiftreg"),
		(t_newmethod)nebulae_shiftreg_new,(t_method)nebulae_shiftreg_free,
		sizeof(t_nebulae_shiftreg), 
		CLASS_NOINLET, 
		A_DEFFLOAT,
		0);
}


