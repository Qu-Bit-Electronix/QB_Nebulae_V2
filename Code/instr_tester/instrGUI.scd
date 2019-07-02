
(

var width = 600, height = 600;
var startKnob, densityKnob, blendKnob, speedKnob, pitchKnob, sizeKnob, overlapKnob, windowKnob;
var recordB, fileB, sourceB, resetB, freezeB;
var upperText;
var background_color = Color.new255(0, 0, 40);
Window.closeAll;
w = Window.new("NEBULAE V2", Rect(0, 0, width, height), false).alwaysOnTop_(true).background_(background_color).front;
upperText = StaticText.new(w, Rect(width/2-50, 20, 100, 20));
upperText.stringColor_(Color.white).string_("Nebulae SC").font_(Font("Yuppy TC", 18));

//PUT SYNTHDEF HERE
	b = Buffer.read(s, Platform.resourceDir +/+ "sounds/a11wlk01.wav"); //audio buffer to be loaded
	SynthDef(\c_phaserFlanger,
		{
			|speed, pitch, start, size, blend, window, overlap, density, bufnum, source, reset, freeze, record|
      //my arguments coming from the nebulae
			var mix = blend.lag(0.1), depth = pitch.linlin(0.0, 1.0, 0.0001, 0.15).lag(0.1), lfospeed = density.linexp(0.0, 1.0, 0.01, 60.0).lag(0.2);
			var feedback = speed.linlin(0.0, 1.0, 0.0, 1).lag(0.1);
			var sig, out, phase, lfo, in, whichBuf, shapes, whichShape;
			var local;
			var delay_time = size.linlin(0.0, 1.0, 0.0001, 0.05).lag(0.1);
			in = Mix.ar([SoundIn.ar(0), SoundIn.ar(1)]);
			whichBuf = Select.ar((BufChannels.kr(bufnum)-1), [Splay.ar(PlayBuf.ar(1, bufnum, 1, 1, 0, 1), 0), PlayBuf.ar(2, bufnum, 1, 1, 0, 1)]);
			sig = Select.ar(source, [whichBuf, in]);
			sig = sig*0.5;
			shapes = [SinOsc.kr(lfospeed).unipolar.range(0.0, depth), LFTri.kr(lfospeed).unipolar.range(0.0, depth), LFCub.kr(lfospeed).unipolar.range(0.0, depth), LFSaw.kr(lfospeed).unipolar.range(0.0, depth)];
			lfo = SelectXFocus.ar(start.linlin(0.0, 1.0, 0.001, 3.0), shapes, 1);
			local = LocalIn.ar(1)+sig;

			4096.do({
				phase = AllpassC.ar((local*feedback)/2, 0.2, delay_time+lfo, overlap.linlin(0.0, 1.0, 0.0, 3.0));
			});

			LocalOut.ar(LPF.ar((phase*feedback), 5000));

			out = Limiter.ar((phase*mix)+((1-mix)*sig));
			Out.ar(0, [out, AllpassN.ar(out, 0.003, window.linlin(0.0, 1.0, 0.0001, 0.0025).lag(0.1), 0)]);



	}).add; //to write a syndef file replace .add with .writeDefFile("/PATH/TO/YOUR/LIKING");
FreqScope.new;
s.scope;
//KNOBS

startKnob = Knob.new(w, Rect(60, 100, 80, 80)).color_([Color.white, background_color, background_color]);
densityKnob = Knob.new(w, Rect(60, 250, 80, 80)).color_([Color.white, background_color, background_color]);
blendKnob = Knob.new(w, Rect(150, 380, 80, 80)).color_([Color.white, background_color, background_color]);


speedKnob = Knob.new(w, Rect(width/2-60, 90, 120, 120)).color_([Color.white, background_color, background_color]);
pitchKnob = Knob.new(w, Rect(width/2-60, 230, 120, 120)).color_([Color.white, background_color, background_color]);

sizeKnob = Knob.new(w, Rect(width-140, 100, 80, 80)).color_([Color.white, background_color, background_color]);
overlapKnob = Knob.new(w, Rect(width-140, 250, 80, 80)).color_([Color.white, background_color, background_color]);
windowKnob = Knob.new(w, Rect(width-230, 380, 80, 80)).color_([Color.white, background_color, background_color]);

//STATIC TEXTS

StaticText.new(w, Rect(width/3.3, 100, 100, 100)).stringColor_(Color.white).string_("speed").font_(Font("Yuppy TC", 18));
StaticText.new(w, Rect(width/3.3, 240, 100, 100)).stringColor_(Color.white).string_("pitch").font_(Font("Yuppy TC", 20));
StaticText.new(w, Rect(width/7.5, 30, 200, 100)).stringColor_(Color.white).string_("start").font_(Font("Yuppy TC", 18));
StaticText.new(w, Rect(width/1.25, 30, 200, 100)).stringColor_(Color.white).string_("size").font_(Font("Yuppy TC", 18));
StaticText.new(w, Rect(width/1.28, 180, 200, 100)).stringColor_(Color.white).string_("overlap").font_(Font("Yuppy TC", 18));
StaticText.new(w, Rect(width/8.25, 180, 200, 100)).stringColor_(Color.white).string_("density").font_(Font("Yuppy TC", 18));
StaticText.new(w, Rect(width/3.6, 310, 200, 100)).stringColor_(Color.white).string_("blend").font_(Font("Yuppy TC", 18));
StaticText.new(w, Rect(width/1.6, 310, 200, 100)).stringColor_(Color.white).string_("window").font_(Font("Yuppy TC", 18));

x = Synth(\c_phaserFlanger, [\source, 0]);
//ACTIONS

startKnob.action_({
	|val|
	x.set(\start, val.value);
});
densityKnob.action_({
	|val|
	x.set(\density, val.value);
});
blendKnob.action_({
	|val|
	x.set(\blend, val.value);
});
speedKnob.action_({
	|val|
	x.set(\speed, val.value);
});
pitchKnob.action_({
	|val|
	x.set(\pitch, val.value);
});
sizeKnob.action_({
	|val|
	x.set(\size, val.value);
});
overlapKnob.action_({
	|val|
	x.set(\overlap, val.value);
});
windowKnob.action_({
	|val|
	x.set(\window, val.value);
});
w.onClose_({x.free; Window.closeAll;});

)
