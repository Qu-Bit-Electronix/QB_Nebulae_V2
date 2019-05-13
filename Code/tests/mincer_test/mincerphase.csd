<CsoundSynthesizer>
<CsOptions>
-odac
-+rtaudio=alsa
-B 2048
-b 512
</CsOptions>
<CsInstruments>
0dbfs = 1.0
sr = 44100
ksmps = 512
nchnls = 2

; Stereo files handled ordinarily programatically.
; For testing:
gSname[] init 100
gSname[0] = "sine.wav"
gSname[1] = "saw.wav"
gSname[2] = "pansines.wav"
gSname[3] = "pansine2.wav"

instr 1

; i-time inits.
iuse_stereo = 1
itest_file =  3 ; 0 = sine, 1 = saw, 2 = pansines (real stereo), 3 = pansines2 (faster fade, no silence)
isource_length filelen gSname[itest_file] ; time in seconds of both audio files.
iright_file_offset = 200
iphaselock = 0
ifftsize = 2048
ihopsize = 16

; ktime setup
kfilesel init 400 + itest_file ; File select. 
klen init isource_length
kpitch = 1.0 
kspeed = 1.00 
;kspeed = 1

; phasor setup
kphasorfreq = 1/klen
aphs phasor 1/klen 
atime = (aphs * klen) * kspeed

; mincer
if iuse_stereo == 0 then
    a1 mincer, atime, 0.75, kpitch, kfilesel, iphaselock, ifftsize, ihopsize
    a2 mincer, atime, 0.75, kpitch, kfilesel, iphaselock, ifftsize, ihopsize
else
    ;a1 mincer, atime, 0.75, kpitch, kfilesel, iphaselock, ifftsize, ihopsize
    ;a2 mincer, atime, 0.75, kpitch, kfilesel + iright_file_offset, iphaselock, ifftsize, ihopsize
    f1 pvstanal, k(atime), 0.75,kpitch, kfilesel
    a1 pvsynth f1
    f2 pvstanal, k(atime),0.75, kpitch, kfilesel + iright_file_offset
    a2 pvsynth f2
endif

; outputs
outs a1, a2
endin

</CsInstruments>
<CsScore>
f 400 0 0 1 "sine.wav" 0 0 1
f 401 0 0 1 "saw.wav" 0 0 1
f 402 0 0 1 "pansines.wav" 0 0 1
f 403 0 0 1 "pansine2.wav" 0 0 1
f 600 0 0 1 "sine.wav" 0 0 2
f 601 0 0 1 "saw.wav" 0 0 2
f 602 0 0 1 "pansines.wav" 0 0 2
f 603 0 0 1 "pansine2.wav" 0 0 2

i1 0 60
</CsScore>
</CsoundSynthesizer>
