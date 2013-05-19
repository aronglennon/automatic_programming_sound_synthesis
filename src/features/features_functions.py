import numpy as np
import struct
from scikits.talkbox.features import mfcc
MAX_LENGTH = 100000

# parse features in file written by max into a numpy array
def get_features(filename,feature_type):
    fileContents = get_audio(filename)
    if feature_type == 'mfcc':
        # get mfcc coeffs and don't look at first (corresponds to energy in signal)
        coeffs = mfcc(fileContents,fs=44100)[0][1:] # [1] is mel coeffs, and [2] is entire FFT data???
    return coeffs

def get_features_from_data(audio_data, feature_type):
    if feature_type == 'mfcc':
        # get mfcc coeffs and don't look at first (corresponds to energy in signal)
        coeffs = mfcc(audio_data,fs=44100)[0][1:] # [1] is mel coeffs, and [2] is entire FFT data???
    return coeffs

def get_audio(filename):
    fileContents = filename.readframes(MAX_LENGTH)
    fileContents = struct.unpack("<%uh" % (len(fileContents) / 2), fileContents)
    fileContents  = np.array(fileContents)/float(np.power(2,16))
    return fileContents