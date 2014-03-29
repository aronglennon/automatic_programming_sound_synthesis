from mysqldb.db_commands import mysql_object
import matplotlib.pyplot as plt
from operator import itemgetter
from pylab import *
from optparse import OptionParser
import os, re
from datetime import datetime
import numpy as np
import wave
from features.features_functions import get_audio

TESTRUN_ID = 575

'''
Parameter Set: TBD once all other tests have been run

The performance of the system is usually measured using the fitness level at which the system converges and how long it takes to converge to that level. 
We have calculated the typical statistics (min, max, mean) over each stopping criteria variation for each individual target as well as all targets combined.
'''

def main():
    font = {'family' : 'normal',
        'weight' : 'bold',
        'size'   : 20}

    matplotlib.rc('font', **font)    
    fig = plt.figure(facecolor='white')
    ax = fig.add_subplot(1, 1, 1)
    plt.title('Evolving Lion Roar Best-of-Run')
    plt.xlabel('Time (s)')
    plt.ylabel('Frequency (Hz)')
    plt.yticks([500, 5000, 10000, 15000, 20000], [0, 5000, 10000, 15000, 20000])
    plt.xticks([0.1, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0], [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
    test_audio_file = wave.open('/Users/aronglennon/automatic_programming_sound_synthesis/wav/Lion-Growling-Mono-2.wav', 'r')
    # get test audio
    test_audio = get_audio(test_audio_file)
    my_specgram(test_audio[0:44100*3], NFFT=512, Fs=44100, noverlap=256, 
                                cmap=None, minfreq = 0, maxfreq = 20000)
    #specgram(test_audio, NFFT=1024, Fs=44100, noverlap=512, cmap=None)
    show()

def my_specgram(x, NFFT=256, Fs=2, Fc=0, detrend=mlab.detrend_none,
             window=mlab.window_hanning, noverlap=128,
             cmap=None, xextent=None, pad_to=None, sides='default',
             scale_by_freq=None, minfreq = None, maxfreq = None, **kwargs):
    """
    call signature::

      specgram(x, NFFT=256, Fs=2, Fc=0, detrend=mlab.detrend_none,
               window=mlab.window_hanning, noverlap=128,
               cmap=None, xextent=None, pad_to=None, sides='default',
               scale_by_freq=None, minfreq = None, maxfreq = None, **kwargs)

    Compute a spectrogram of data in *x*.  Data are split into
    *NFFT* length segments and the PSD of each section is
    computed.  The windowing function *window* is applied to each
    segment, and the amount of overlap of each segment is
    specified with *noverlap*.

    %(PSD)s

      *Fc*: integer
        The center frequency of *x* (defaults to 0), which offsets
        the y extents of the plot to reflect the frequency range used
        when a signal is acquired and then filtered and downsampled to
        baseband.

      *cmap*:
        A :class:`matplotlib.cm.Colormap` instance; if *None* use
        default determined by rc

      *xextent*:
        The image extent along the x-axis. xextent = (xmin,xmax)
        The default is (0,max(bins)), where bins is the return
        value from :func:`mlab.specgram`

      *minfreq, maxfreq*
        Limits y-axis. Both required

      *kwargs*:

        Additional kwargs are passed on to imshow which makes the
        specgram image

      Return value is (*Pxx*, *freqs*, *bins*, *im*):

      - *bins* are the time points the spectrogram is calculated over
      - *freqs* is an array of frequencies
      - *Pxx* is a len(times) x len(freqs) array of power
      - *im* is a :class:`matplotlib.image.AxesImage` instance

    Note: If *x* is real (i.e. non-complex), only the positive
    spectrum is shown.  If *x* is complex, both positive and
    negative parts of the spectrum are shown.  This can be
    overridden using the *sides* keyword argument.

    **Example:**

    .. plot:: mpl_examples/pylab_examples/specgram_demo.py

    """

    #####################################
    # modified  axes.specgram() to limit
    # the frequencies plotted
    #####################################

    # this will fail if there isn't a current axis in the global scope
    ax = gca()
    Pxx, freqs, bins = mlab.specgram(x, NFFT, Fs, detrend,
         window, noverlap, pad_to, sides, scale_by_freq)

    # modified here
    #####################################
    if minfreq is not None and maxfreq is not None:
        Pxx = Pxx[(freqs >= minfreq) & (freqs <= maxfreq)]
        freqs = freqs[(freqs >= minfreq) & (freqs <= maxfreq)]
    #####################################

    Z = 10. * np.log10(Pxx)
    Z = np.flipud(Z)

    if xextent is None: xextent = 0, np.amax(bins)
    xmin, xmax = xextent
    freqs += Fc
    extent = xmin, xmax, freqs[0], freqs[-1]
    im = ax.imshow(Z, cmap, extent=extent, **kwargs)
    ax.axis('auto')

    return Pxx, freqs, bins, im

if __name__ == "__main__":
    main()
    
