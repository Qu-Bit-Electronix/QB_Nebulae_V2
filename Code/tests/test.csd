<CsoundSynthesizer>
<CsOptions>
;-odac:hw:0,0
-odac
-B 2048
-b 128
;-o wave.wav
;-+rtaudio=alsa
</CsOptions>
<CsInstruments>
0dbfs = 1.0
sr = 48000
ksmps = 64
nchnls = 2

instr 1
a0 = 0
a1 vco2 0.8, 200
outs a0, a1
endin

</CsInstruments>
<CsScore>
i1 0 10
</CsScore>
</CsoundSynthesizer>
