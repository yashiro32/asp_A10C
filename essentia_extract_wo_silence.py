import os

import essentia
import essentia.standard as ess
import essentia.streaming

import numpy as np

import matplotlib.pyplot as plt

fpaths = []
labels = []
spoken = []
folders = []
for f in os.listdir('testDownload'):
    for w in os.listdir('testDownload/' + f):
        if os.path.isdir('testDownload/' + f + '/' + w):
            folders.append(w)
            for music in os.listdir('testDownload/' + f + '/' + w):
                if music.endswith('.mp3'):
                    fpaths.append('testDownload/' + f + '/' + w + '/' + music)  
                    labels.append(f)
                    if f not in spoken:
                        spoken.append(f)

#print 'Words spoken:',spoken
#print len(fpaths)
#print len(labels)
#print len(folders)

descriptors       = { 0: 'lowLevel.spectral_centroid',
                      1: 'lowLevel.dissonance',
                      2: 'lowLevel.hfc',
                      3: 'sfx.logattacktime',
                      4: 'sfx.inharmonicity',
                      5: 'lowLevel.spectral_contrast',
                      6: 'lowLevel.mfcc'
                    }

M = 1024
N = 1024
H = 512
fs = 44100
spectrum = ess.Spectrum(size=N)
window = ess.Windowing(size=M, type='hann')
spectralpeaks = ess.SpectralPeaks(orderBy="frequency",
                              magnitudeThreshold=1e-05,
                              minFrequency=40,
                              maxFrequency=5000, 
                              maxPeaks=10000)
envelope = ess.Envelope()

mfcc = ess.MFCC(numberCoefficients = 40, inputSize = N/2+1)
cent = ess.Centroid()
sc = ess.SpectralContrast(frameSize = N)
hfc = ess.HFC()
dissonance = ess.Dissonance()
LAT = ess.LogAttackTime()
Inharm = ess.Inharmonicity()

energy = ess.Energy()
rms = ess.RMS()

extractor = ess.Extractor()

c = 0

for n,file in enumerate(fpaths):
    x = ess.MonoLoader(filename=file, sampleRate = fs)()
    
    pool = essentia.Pool()
    
    mfccs = np.array([])
    eners = np.array([])
    
    for frame in ess.FrameGenerator(x, frameSize=M, hopSize=H, startFromZero=True):
        
        ener = energy(frame)
        eners = np.append(eners, ener)

        if ener > 0.01:
            mX = spectrum(window(frame))

            mfcc_bands, mfcc_coeffs = mfcc(mX)
        
            #if len(mfccs) == 0:
                #mfccs = mfcc_coeffs
            #else:
                #mfccs = np.vstack((mfccs, mfcc_coeffs))

            pool.add('lowLevel.mfcc', mfcc_coeffs)
            
            centroid = cent(mX)
            pool.add('lowLevel.spectral_centroid', centroid)

            contrast, valley = sc(mX)
            pool.add('lowLevel.spectral_contrast', contrast)

            hf = hfc(mX)
            pool.add('lowLevel.hfc', hf)

            freqs, peaks = spectralpeaks(mX)
            diss = dissonance(freqs, peaks)
            pool.add('lowLevel.dissonance', diss)

            enve = envelope(frame)
            lat = LAT(enve)
            pool.add('sfx.logattacktime', lat)

            inharm = Inharm(freqs, peaks)            
            pool.add('sfx.inharmonicity', inharm)

    """if c == 137:
        plt.plot(eners)
        plt.show()"""

    #pool = extractor(x)
    
    #mfccs_mean = np.mean(mfccs, axis=0)
    # Compute mean and variance of the frames
    aggrPool = ess.PoolAggregator(defaultStats = ['mean'])(pool)

    # And output those results in a file
    start_folder = 'essentiaDownload3/'
    if not os.path.exists(start_folder + labels[c]):
        os.makedirs(start_folder + labels[c])
    if not os.path.exists(start_folder + labels[c] + '/' + folders[c]):
        os.makedirs(start_folder + labels[c] + '/' + folders[c])
    ess.YamlOutput(filename = start_folder + labels[c] + '/' + folders[c] + '/' + folders[c] + '.json', format='json')(aggrPool)

    c += 1


    
        

    
