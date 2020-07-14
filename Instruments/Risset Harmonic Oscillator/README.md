# Risset Harmonic Oscillator

Nine oscillators tuned to very small offsets relative to the main pitch create an effect called "Risset's harmonic arpeggio", named for electronic music pioneer Jean-Claude Risset, who discovered this technique (and many others besides) and created much beautiful music.

The usual implementation, as used here, has one oscillator tuned to the main pitch, four oscillators tuned slghtly sharp in relation to the main pitch, and four oscillators tuned slightly flat in relation to the main pitch. When these oscillators are combined, we hear a single pitch with cascading harmonics (Risset called this "spectral sweeping").

For detailed information about the Risset harmonic arpeggio, including sample Csound code, see Reginald Bain's excellent article from the Csound Journal (Issue 17, Fall 2012): http://www.csounds.com/journal/issue17/bain_risset_arpeggio.html

## Controls

 * Pitch (Pitch knob or v/oct CV input)
 * Amplitude (Start kbob or CV input)
 * Harmonic arpeggiation offset size (Size knob or CV input)
 * Waveform (Density knob or CV input)
 * Cross-Panning Speed (Overlap knob or CV input) - STEREO MODE ONLY
 * Stereo/dual-mono selection (Record button)

## Details

This instrument is a wavetable oscillator that has the Risset harmonic arpeggio built in. By defult, it has stereo outputs, with the main pitch plus the even-numbered offsets in the left channel and the main picth plus the odd-numbered offsets in the right channel. There is also an optional dual mono mode, with the complete Risset arpeggio in channel 1 (L) and the main pitch only in channel 2 (R); this is selected using the Record button (which latches).

You can control the arpeggio effect using the Size knob (or CV input) which sets the detuning amount. This ranges from 0.001 Hz to 0.03 Hz, and determines the speed of the harmonic sweep.

You can control the pitch using the Pitch knob, but you can also use the v/oct CV input. You can control amplitude using the Start knob, or you can use the associated CV input with any CV source that produces an envelope.

Waveform is controlled by the Density knob (or CV input). This control morphs smoothly through six waveforms. The first three are the familiar triangle (at full CCW), sawtooth, and square. The other three are non-standard: David First's asymptotic sawtooth, prime (prime-numbered partials up to the 31st harmonic), and fibonnaci (partials in the Fibonnaci sequence up to the 34th harmonic, at full CW).

There is an optional cross-panning effect (only in stereo mode) that pans the two channels back and forth, each channel with its own LFO. The LFOs begin with opposite phase, operate at very slightly different speeds and move in opposite directions. The panning speed is controlled by the Overlap knob. This provides a kind of tremolo, most apparent at higher speeds. At slower speeds, it animates the output.

## Thanks

 * Jean-Claude Risset (RIP) for all of his contributions
 * The Csound user community (especially Jeanette C., who suggested wavetable morphing).
 * The Technobear, whose firmware was very helpful udring the development process.
 * Reginald Bain for his article. I've been playing with this technique since 2004, but I learned a lot from the article.

## Changelog
 * v1.0 - initial release
 * v1.1 - bugfix

---

Dave Seidel, June 2020, v1.1