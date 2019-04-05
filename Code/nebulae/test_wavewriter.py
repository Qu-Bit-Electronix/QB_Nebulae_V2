import wavewriter
import numpy as np
import matplotlib.pylab as plt

writer = wavewriter.WaveWriter()

freq = 440.0
sr = 48000.0
phs_inc = (2.0 * np.pi * freq) / sr
phs = 0.0
t = 5.0

datal = np.empty([int(sr*t),1])
datar = np.empty([int(sr*t),1])

# Fill data
for i in range(int(sr*t)):
    datal[i] = np.sin(phs) * 32767.0
    datar[i] = np.sin(phs) * 32767.0
    phs += phs_inc
    if (phs > np.pi * 2.0):
        phs -= (np.pi * 2.0)

writer.WriteStereoWaveFile(datal, datar)
