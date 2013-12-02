# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
#    utils.py
#
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

import numpy as np
import subprocess
import wave
import os
import tempfile as tmp
from acousim import _tempdir, _kWAVE_EXT

def temp_wavfile():
    """
    Returns
    -------
    tmpfile : string    
        A writeable wavefile path.
    """
    
    return tmp.mktemp(suffix='.'+_kWAVE_EXT,dir=_tempdir)

def trim(fin, fout, tstart, tstop, VERBOSE = False):
    """
    Excerpt a clip from a sound file, given a set of time points.
    
    Parameters
    ----------
    fin : str
        sound file to excerpt
    
    fout : str
        file to save output as
    
    tstart : float
        clip start time in fin
    
    tstop : float
        clip stop time in fin
        
    VERBOSE : boolean (opt)
        toggle console printing
    
    
    Returns
    -------
    None
    """
    sox_list = ['sox', fin, fout, 'trim',
                '%0.3f'%tstart,'%0.3f' % (tstop - tstart)]
    try:
        if VERBOSE:
            print("Executing: " + " ".join(sox_list))
        p = subprocess.Popen(sox_list)
        sts = p.wait()
        if VERBOSE:
            print sts    
    except OSError, e:
        print('SoX execution failed: %s'%e)
    

def convert(filename, fout=None, samplerate=None, channels=None, bitdepth=None):
    """
    Convert a given file to a temporary wave object.
    
    Parameters
    ----------
    filename : str
        file to convert
        
    fout : str (optional)
        filename to use... if none is provided, a timestamped
        temp name is created. Note: whatever this filename ends up
        being, it is saved as a object member obj._abspath
    
    samplerate : float (optional)
    channels : int (optional)
    bitdepth : int (optional)
    
    
    Returns
    -------
    wavefile : wave object
        note that this object is already opened
    
    """
    
    sox_list = ['sox','-V1', '--no-dither',filename]
    
    if bitdepth:
        sox_list += ['-b %d'%bitdepth]
    if channels :
        sox_list += ['-c %d'%channels]
    if fout is None:
        fout = temp_wavfile()
        
    sox_list += [fout]
    
    if samplerate:
        sox_list += ['rate','-I', '%f'%samplerate]
    
    try:
        p = subprocess.Popen(sox_list)
        sts = p.wait()
        wavefile = wave.open(fout, 'r')
    except OSError, e:
        print('SoX failed! %s'%e)
    except TypeError, e:
        print("Error executing: %s"%" ".join(sox_list))
        raise TypeError(e)
    
    wavefile._abspath = fout
    return wavefile


def is_valid_sox_format(ext, VERBOSE=False):
    """
    Check to see if SoX supports a given file extension.
    
    Parameters
    ----------
    ext : str
        audio file extension to verify
        
    VERBOSE : boolean (opt)
        toggle console printing
    
    
    Returns
    -------
    valid : boolean
        format compatibility
    """
    
    valid = False
    msg = os.popen('sox -h').readlines()
    for m in msg:
        if m.count('AUDIO FILE FORMATS')>0:
            valid = ext in m
            if VERBOSE:
                print m
    
    return valid


def is_valid_format(filename, VERBOSE=False):
    """
    Check to see if a given file type is supported.
    
    Parameters
    ----------
    filename : str
        audio file to verify for support
        
    VERBOSE : boolean (opt)
        toggle console printing
    
    
    Returns
    -------
    valid : boolean
        compatibility flag
    """
    
    fext = os.path.splitext(filename)[-1][1:]
    
    # Pure wave support
    if fext == 'wav':
        return True
    
    # Otherwise, SoX?
    else:
        valid = is_valid_sox_format(ext=fext, VERBOSE=VERBOSE) 
        if VERBOSE and not valid:
            print("Sorry, SoX currently doesn't support conversion to / from '%s' files." % fext)
        return valid


def tri_flat(array, UPPER=True):
    """
    Flattens the upper/lower triangle of a square matrix.
    
    Parameters
    ----------
    array : np.ndarray
        square matrix
        
    UPPER : boolean
        Upper or lower triangle to flatten (defaults to upper). If
        the matrix is symmetric, this parameter is unnecessary.
    
    Returns
    -------
    array : np.ndarray
        vector representation of the upper / lower triangle
    """
    
    C = array.shape[0]
    if UPPER:
        mask = np.asarray(np.invert(np.tri(C,C,dtype=bool)),dtype=float)
    else:
        mask = np.asarray(np.invert(np.tri(C,C,dtype=bool).transpose()),dtype=float)
        
    x,y = mask.nonzero()
    return array[x,y]

def sox_call(sox_list, VERBOSE=False):
    try:
        if VERBOSE:
            print("Executing: " + " ".join(sox_list))
        p = subprocess.Popen(sox_list)
        sts = p.wait()
        if VERBOSE:
            print sts    
    except OSError, e:
        print('SoX execution failed: %s'%e)