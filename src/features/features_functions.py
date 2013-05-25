import numpy as np
import struct, wave
from scikits.talkbox.features import mfcc
from acousim.transforms import timbrespace
MAX_LENGTH = 1000000

# parse features in file written by max into a numpy array
def get_features(filename,feature_type):
    if feature_type == 'mfcc':
        test_audio_file = wave.open(filename, 'r')
        fileContents = get_audio(test_audio_file)
        # get mfcc coeffs and don't look at first (corresponds to energy in signal)
        coeffs = mfcc(fileContents,fs=44100)[0][1:] # [1] is mel coeffs, and [2] is entire FFT data???
    elif feature_type == 'nlse':
        coeffs = timbrespace(filename)        # default hopsize=3, i.e. 50%, i.e. 150 ms
    return coeffs

'''
NO LONGER USED
def get_features_from_data(audio_data, feature_type):
    if feature_type == 'mfcc':
        # get mfcc coeffs and don't look at first (corresponds to energy in signal)
        coeffs = mfcc(audio_data,fs=44100)[0][1:] # [1] is mel coeffs, and [2] is entire FFT data???
    return coeffs
'''

def get_audio(filename):
    fileContents = filename.readframes(MAX_LENGTH)
    fileContents = struct.unpack("<%uh" % (len(fileContents) / 2), fileContents)
    fileContents  = np.array(fileContents)/float(np.power(2,16))
    return fileContents