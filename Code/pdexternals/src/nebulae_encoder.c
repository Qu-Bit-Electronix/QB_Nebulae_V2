/*
 * PD external for using the encoders on the nebulae.
 * Takes an argument 0 or 1 (later to be "speed" or "pitch")
 * Three Outlets - Up tick, Down tick, pressed state
 */
#include "m_pd.h"
#include <stdio.h>
#ifdef __arm__
	#include <wiringPi.h>
#endif

t_class *nebulae_encoder_class;

typedef struct _nebulae_encoder
{
	t_object x_obj;
	t_clock *x_clock;
    t_int aState;
    t_int bState;
	t_int pressState;
	t_int prevPressState;
	t_int pinNumA;
    t_int pinNumB;
    t_int pinNumClick;
    t_int qds[2];
	t_outlet *x_out_up;
	t_outlet *x_out_down;
	t_outlet *x_out_press;

} t_nebulae_encoder;

void nebulae_encoder_bang(t_nebulae_encoder *x)
{
	#ifdef __arm__
        x->prevPressState = x->pressState;
		x->pressState = digitalRead(x->pinNumClick); 
		x->aState = digitalRead(x->pinNumA); 
		x->bState = digitalRead(x->pinNumB); 
	#endif
    // Debounce
    x->qds[0] = (x->qds[0] << 1) | x->aState;
    x->qds[1] = (x->qds[1] << 1) | x->bState;
    // Decode
    if ((x->qds[0] & 0x03) == 0x02 && (x->qds[1] & 0x03) == 0x00) {
        outlet_bang(x->x_out_up);
    } else if ((x->qds[1] & 0x03) == 0x02 && (x->qds[0] & 0x03) == 0x00) {
        outlet_bang(x->x_out_down); 
    }
    if (x->pressState != x->prevPressState) {
        outlet_float(x->x_out_press, x->pressState);
    }
	//clock_delay(x->x_clock, 0x1); 
    //clock_delay(x->x_clock, 0x5);
}

void *nebulae_encoder_new(t_floatarg _enc)
{
	t_nebulae_encoder *x = (t_nebulae_encoder *)pd_new(nebulae_encoder_class);
	//x->x_clock = clock_new(x, (t_method)nebulae_encoder_tick);
	// valid pin?
    if (_enc == 1) {
        // Pitch Encoder
        x->pinNumA = 17;
        x->pinNumB = 27;
        x->pinNumClick = 22;
    } else {
        // Speed Encoder
        x->pinNumA = 13;
        x->pinNumB = 19;
        x->pinNumClick = 26;
    }
	#ifdef __arm__
		pinMode(x->pinNumA, INPUT);
		pullUpDnControl(x->pinNumA, PUD_UP);
		pinMode(x->pinNumB, INPUT);
		pullUpDnControl(x->pinNumB, PUD_UP);
		pinMode(x->pinNumClick, INPUT);
		pullUpDnControl(x->pinNumClick, PUD_UP);
	#endif
	x->x_out_up = outlet_new(&x->x_obj, gensym("bang"));
	x->x_out_down = outlet_new(&x->x_obj, gensym("bang"));
	x->x_out_press = outlet_new(&x->x_obj, gensym("float"));
	//nebulae_encoder_tick(x);
	return (void *)x;
}

void nebulae_encoder_free(t_nebulae_encoder *x)
{
	//clock_free(x->x_clock);
	outlet_free(x->x_out_up);  
    outlet_free(x->x_out_down);
    outlet_free(x->x_out_press);
}

void nebulae_encoder_setup()
{
	#ifdef __arm__
		wiringPiSetupGpio();
	#endif	
	nebulae_encoder_class = class_new(gensym("nebulae_encoder"),
		(t_newmethod)nebulae_encoder_new, (t_method)nebulae_encoder_free,
		sizeof(t_nebulae_encoder), 
		0, 
		A_DEFFLOAT,
		0);
    class_addbang(nebulae_encoder_class, nebulae_encoder_bang);
}


