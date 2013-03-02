'''
Created on Jul 11, 2012

@author: apg250
'''
import pickle
import numpy as np
from features import features_functions

def main():
    pickleFileName = '/etc/max/results_target.npy'
    pickleFile = open(pickleFileName, 'wb')
    file = open('/etc/max/results_target.txt', 'rb')
    featureArray = features_functions.get_features(file)
    pickle.dump(featureArray,pickleFile)
    
if __name__ == "__main__":
    main() 