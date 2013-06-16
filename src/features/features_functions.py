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
        test_audio_file.close()
    elif feature_type == 'nlse':
        coeffs = timbrespace(filename)        # default hopsize=3, i.e. 50%, i.e. 150 ms
    return coeffs

def get_audio(filename):
    fileContents = filename.readframes(MAX_LENGTH)
    fileContents = struct.unpack("<%uh" % (len(fileContents) / 2), fileContents)
    fileContents  = np.array(fileContents)/float(np.power(2,16))
    return fileContents

def main():
    FILENAMES = ['/Users/apg250/git/automatic_programming_sound_synthesis/max_patches/realworld_sounds/for_testing/Metal_Gong-Mono.wav', 
                 '/Users/apg250/git/automatic_programming_sound_synthesis/max_patches/realworld_sounds/for_testing/Freight_Train-Mono.wav',
                 '/Users/apg250/git/automatic_programming_sound_synthesis/max_patches/realworld_sounds/for_testing/Lion-Growling-Mono.wav',
                 '/Users/apg250/git/automatic_programming_sound_synthesis/max_patches/realworld_sounds/for_testing/RandomAnalogReverb-Ballad-Mono.wav',
                 '/Users/apg250/git/automatic_programming_sound_synthesis/max_patches/realworld_sounds/for_testing/Synth-Metallic-IDM-Pad-Mono.wav']
               
    for f in FILENAMES:     
        test_features = get_features(f, 'nlse')
        for t in test_features:
            print t
    
if __name__ == '__main__':
    main()
