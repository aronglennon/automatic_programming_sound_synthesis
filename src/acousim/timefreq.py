'''
Created on May 7, 2013

@author: ejhumphrey
'''

import numpy as np
import struct
import wave
import os

import acousim.utils as utils
from numpy.fft.fftpack import rfft

kMAX_FULL_WAVEFORM_LENGTH = 10*60*44100     # 10 minute file at 44.1 kHz

DEFAULT_CQT_PARAMS = {'framerate':20.0,
                      'Q':1.0,
                      'bins_per_octave':24,
                      'freq_max':7040.,
                      'octaves':7,
                      'channels':1,
                      'framemode':'center',
                      'VERBOSE':False,
                      'log_coeff':50.0}


# --- Helper methods --- 
def _rawdata_to_array(data, channels, bytedepth):
    """
    Convert packed byte string into numpy arrays
    
    Parameters
    ----------
    frame : string
        raw byte string
    channels : int
        number of channels to unpack from frame
    bytedepth : int
        byte-depth of audio data
    
    Returns
    -------
    frame : np.ndarray of floats
        array with shape (N,channels), bounded on [-1.0, 1.0)
    """
    
    N = len(data) / channels / bytedepth
    fmt = 'h' # Assume 2-byte
    if bytedepth==3:
        tmp = list(data)
        [tmp.insert(k*4+3,struct.pack('b',0)) for k in range(N)];
        data = "".join(tmp)
    if bytedepth in [3,4]:
        fmt = 'i'
    
    frame = np.array(struct.unpack('%d%s' % (N,fmt) * channels, data)) / (2.0 ** (8 * bytedepth - 1))
    return frame.reshape([N, channels])

def _array_to_rawdata(frame, channels, bytedepth):
    """
    Convert numpy arrays into writable raw byte strings
    
    Parameters
    ----------
    frame : np.ndarray
        array with shape (N,channels), bounded on [-1.0, 1.0)
    channels : int
        number of channels to interpret from frame; higher 
        priority over the 2nd dimension of 'frame'
    bytedepth : int
        byte-depth of audio data
    
    Returns
    -------
    data : str 
        raw byte string
    """
    
    N = len(frame) * channels
    frame = np.asarray(frame.flatten()*(2.0 ** (8 * bytedepth - 1)), dtype = int)
    frame = struct.pack('%dh' % N, *frame)
    return frame


# CQ Kernel matrix
def cq_kernel2(q,fmin,octaves,samplerate,bins_per_octave):
    fmax = np.power(2.0,octaves)*fmin
    oct_low = 0
    oct_high = np.log2(fmax/float(fmin))
    num_steps = int((oct_high)*bins_per_octave + 0.5)+1
    f_basis = np.logspace(start=oct_low,
                          stop=oct_high,
                          num=num_steps,
                          base=2)*fmin
    a_basis = []
    N_max = -1
    # It's always going to come in one-hot
    for f_k in f_basis[:-1]:
        N_k = np.round((q*samplerate) / (f_k * (np.power(2.0, 1./bins_per_octave) - 1)))
        a_k = np.sqrt(np.hanning(int(N_k)))/N_k*np.exp(2j*np.pi*f_k/samplerate*np.arange(int(N_k)))
#        a_k = np.hanning(int(N_k))*np.exp(2j*np.pi*f_k/samplerate*np.arange(int(N_k)))
#        a_k = np.exp(2j*np.pi*f_k/samplerate*np.arange(int(N_k)))
        a_basis += [a_k]
        if N_k > N_max:
            N_max = N_k
    
    K = len(a_basis)
    N_log2 = int(np.power(2,np.ceil(np.log2(N_max))))
    a_matrix = np.zeros([K, N_log2], dtype=np.complex)
    for k in range(K):
        N_k = len(a_basis[k])
        n_0 = int((N_log2 - N_k)/2.0)
        a_matrix[k,n_0:n_0+N_k] = a_basis[k]
    return np.fft.fft(a_matrix,axis=1)[:,:N_log2/2+1]


# --------- Class Definitions ---------
class AudioFile(object):
    
    def __init__(self, filename, **kwargs):
        
        self.params = {'samplerate':44100.0,
                       'channels':1,
                       'bitdepth':16,
                       'VERBOSE':False}
        
        self._filename = filename
        self._wavefile = None
        self.update_params(**kwargs)
        
        try:
            assert utils.is_valid_format(filename, self.verbose())
        except AssertionError:
            utils.is_valid_format(filename, VERBOSE=True)
            raise AssertionError("Error: Unsupported audio file format.")
        
    def close(self):
        """
    Perform a thorough clean-up. Explict method called by built-in __del__()
            
    Returns
    -------
    None
         
        """
        if not self._wavefile is None:
            self._wavefile.close()
            if(self._CONVERT):
                os.remove(self._wavefile._abspath)
        
    def __del__(self):
        if not self._wavefile is None:
            self.close()
    
    # --- Setter ---
    def update_params(self, **kwargs):
        """
       Subclass me!
        """
        self.params.update(kwargs)
        if self.verbose():
            self.usage()
    
    # --- Getters --- 
    def samplerate(self):
        """
    Returns
    -------
    samplerate : float
        """
        if self.params['samplerate']:
            return float(self.params['samplerate'])
    
    def channels(self):
        """
    Returns
    -------
    channels : int
        number of audio channels
        """
        if self.params['channels']:
            return int(self.params['channels'])
    
    def bitdepth(self):
        """
    Returns
    -------
    bitdepth : int
        bits per sample
        """
        if self.params['bitdepth']:
            return int(self.params['bitdepth'])
    
    def filename(self):
        """
    Returns
    -------
    fpath : string
        file path that was provided to the constructor
        
        """
        return self._filename
    
    def wavefile(self):
        """
    Returns
    -------
    fpath : string
        absolute file path to the wavefile read by this object 
        
        """
        if self._wavefile is None:
            return self._wavefile
        return self._wavefile._abspath
    
    def verbose(self):
        """
    Returns
    -------
    verbose : bool
        """
        return self.params['VERBOSE']
    
        
class FramedAudioFile(AudioFile):
    
    def __init__(self, filename, **kwargs):
        
        self.params = {'framesize':None,
                       'framemode':'left',
                       'frameoffset':0,
                       'hopsize':None,
                       'framerate':None,
                       'overlap':0.0,
                       'samplerate':None,
                       'channels':None,
                       'bitdepth':None,
                       'read_times':None,
                       'VERBOSE':False}
        
        self.update_params(**kwargs)
        AudioFile.__init__(self, filename, **self.params)
        
        # Default hanning window
        self.window = None
        if self.params.get('framesize'):
            self.window = np.hanning( self.framesize() )
            self.window /= self.window.sum()/2.0      
            self.window = self.window[:,np.newaxis]
        
        
    # --- Setter ---
    def update_params(self, **kwargs):
        """        
    Parameters
    ----------
    framerate : float
    
    framemode : string
        one of ['left', 'right', 'center']
    
    frameoffset : float
    
    channels : int 
    
    bitdepth : int
    
    framesize : int
    
    overlap : float
    
    hopsize : float
    
    read_times : array_like
    
        """
        self.params.update(kwargs)
        if not (self.params.get('framerate') is None) and not (self.params.get('samplerate') is None):
            self.params['hopsize'] = self.samplerate() / self.framerate()
        elif not (self.params.get('overlap') is None) and (not self.params.get('framesize') is None):
            self.params['hopsize'] = self.framesize()*(1.0 - self.params.get('overlap'))
        
        if self.verbose():
            print "%s : Current Parameters"%self.__class__.__name__
            for k in self.params:
                print k, self.params[k]
        
        
    # --- Getters ---
    def numframes(self):
        """    
    Returns
    -------
    nframes : int
        number of frames in the audiofile
        """
        if self.params['read_times'] is None:
            return int(np.ceil((self.numsamples() - self.frameoffset()) / float(self.hopsize())))
        else:
            return len(self.params['read_times'])
    
    def framesize(self):
        """
    Returns
    -------
    framesize : int
        number of samples returned per frame
        """
        if self.params.get('framesize'):
            return int(self.params.get('framesize'))
        else:
            raise ValueError("Framesize is not set! Init with a framesize or use set_params(framesize=?) to correct.")
    
    def framerate(self):
        """        
    Returns
    -------
    framerate : float
        frequency of frames, in Hertz
        """
        if self.params.get('framerate'):
            return float(self.params.get('framerate'))
        
        else: # Fallback to hopsize
            return self.samplerate() / float(self.hopsize())
    
    def frameshape(self):
        """
    Returns
    -------
    shape : tuple
        tuple of (frame length, number of channels)

        """
        return (self.framesize(), self.channels())
    
    def framemode(self):
        """
    Returns
    -------
    mode : string
        alignment mode, one of ['left','center','right']
        """
        return self.params.get('framemode')
    
    def frameoffset(self):
        """
    Returns
    -------
    offset : int
        Frame offset, in samples
        """
        offset = 0
        if self.framemode() == 'center':
            offset -= 0.5*self.framesize()
        elif self.framemode() == 'right':
            offset -= self.framesize()
        
        return int(offset + self.params.get('frameoffset')) 
    
    def hopsize(self):
        """
    Returns
    -------
    hopsize : float
        Number of samples between adjacent frames.
        
        """
        return self.params.get('hopsize')
    
    def overlap(self):
        """
    Returns
    -------
    overlap : float
        Overlap between frames, as a ratio of the framesize
        
        """
        return (self.framesize() - self.hopsize()) / float(self.framesize())
    
    def duration(self):
        """
    Returns
    -------
    dur : float
        duration of the audiofile, in seconds
        
        """
        return self.numsamples() / self.samplerate()
    
    def numsamples(self):
        """
    Returns
    -------
    n : int
        number of samples in the file
        
        """
        samps = self._wavefile.getnframes()
        if samps > 0:
            return samps
        else:
            raise ValueError("Number of samples not contained in file header!")
        
    def read_times(self):
        """
        """
        return self.params.get('read_times')
    
class AudioReader(FramedAudioFile):
    """
    """
    
    def __init__(self, filename, **kwargs):
        
        self.params = {'framesize':4096,
                       'framemode':'left',
                       'frameoffset':0,
                       'hopsize':None,
                       'overlap':0.0,
                       'framerate':None,
                       'samplerate':None,
                       'channels':None,
                       'bitdepth':None,
                       'read_times':None,
                       'VERBOSE':False}
        
        self.update_params(**kwargs)
        FramedAudioFile.__init__(self, filename, **self.params)
        
        # See if we need to SoX this
        self._CONVERT = False    
        try:
            self._wavefile = wave.open(self._filename, 'r')
            if((self._wavefile.getsampwidth()*8 != self.bitdepth() ) & (self.bitdepth() is not None)):
                self._CONVERT = True
            if((self._wavefile.getframerate() != self.samplerate()) & (self.samplerate() is not None)):
                self._CONVERT = True
            if((self._wavefile.getnchannels() != self.channels()) & (self.channels() is not None)):
                self._CONVERT = True
        except wave.Error:
            self._CONVERT = True
         
        # File format conversion check
        if(self._CONVERT):
            self._wavefile = utils.convert(self._filename,
                                               samplerate=self.samplerate(),
                                               bitdepth=self.bitdepth(),
                                               channels=self.channels())
        # - - - - END.if - - - -  
        
        # Overwrite with actual params
        self.update_params(channels = self._wavefile.getnchannels(),
                           bitdepth = self._wavefile.getsampwidth() * 8,
                           samplerate = self._wavefile.getframerate())
        
        if self.verbose():
            print("AudioReader Parameters:")
            print("  Conversion Necessary: %s"%self._CONVERT)
            if self._CONVERT:
                print("  Temp File: %s."%self._wavefile._abspath)
                
        self.reset()
        
    def reset(self):
        """
    Set the file's read pointer back to zero & take care of
    initialization.
    
    Returns
    -------
    None
        """
        self._EOF=False
        self.set_read_times(self.read_times())
        self.framebuffer = np.zeros(self.frameshape())
    
    def set_read_times(self, read_times):
        """
    Establish a vector of read indexes for pulling from an audiofile.
    
    Parameters
    ----------
    read_ptrs : array_like
        vector of read times or indexes
        
    is_time : bool=False
        toggle between sample and time indices
        
    Returns
    -------
    None
    
        """
        if read_times is None:
            # if not given, default to fixed frames
            read_times = np.arange(self.numframes(),dtype=float)/self.framerate()
        
        self.params['read_times'] = np.asarray(read_times) 
        read_ptrs = np.asarray(self.read_times()*self.samplerate(), dtype=int) + self.frameoffset()
        self._read_idxs = read_ptrs
        self._read_pointer = 0
    
    # --- Read Methods ---
    def read_frame_at_index(self, sample_idx, framesize=None):
        """
    Given a sample index and a frame length, read data directly from a 
    wave file. 
    
    Parameters
    ----------
    sample_idx : int
        starting sample index to read from
        
    framesize : int=None
        number of samples to return, if None uses the current default
        
    
    Returns
    -------
    x : np.ndarray
        signal array with shape (time, channels)
        
        """
        if framesize is None:
            framesize = self.framesize()
        
        frame_idx = 0
        frame = np.zeros([framesize,self.channels()])
        
        # Check boundary conditions
        if sample_idx < 0 and sample_idx + framesize > 0:
            framesize = framesize - np.abs(sample_idx)
            frame_idx = np.abs(sample_idx)
            sample_idx = 0
        elif sample_idx > self.numsamples():
            return frame
        elif (sample_idx + framesize) < 0:
            return frame
            
        self._wavefile.setpos(sample_idx)
        newdata = _rawdata_to_array(self._wavefile.readframes(int(framesize)),
                                    self.channels(),
                                    self._wavefile.getsampwidth())
        N = newdata.shape[0]
        # Place new data within the frame
        frame[frame_idx:frame_idx+N] = newdata
        return frame
    
    def read_frame_at_time(self, time_idx, framesize=None):
        """
    Read a frame of data at an arbitrary time point in the file.
    
    Parameters
    ----------
    time_idx : float
        start read time, in seconds
        
    framesize : int=None
        number of samples to return, if None uses the current default
    
    Returns
    -------
    x : np.ndarray
        signal array with shape (time, channels)
    
        """
        sample_idx = int(np.round(time_idx*self.samplerate()))
        return self.read_frame_at_index(sample_idx, framesize)
     
    def update_framebuffer(self):
        """
    Updates the internal 'frame_buffer' data structure (a numpy array)
    
    Returns
    -------
    status : bool
        True if successful, False otherwise. If unsuccessful, the 
        framebuffer is cleared to prevent *really* bad things 
        from happening.
    
        """
        if not self._EOF:
            sample_idx = self._read_idxs[self._read_pointer]
            self._read_pointer += 1
            if self._read_pointer >= len(self._read_idxs):
                self._EOF = True
            self.framebuffer[:,:] = self.read_frame_at_index(sample_idx)
            return True
        
        self.framebuffer[:,:] = 0.0
        return False
        
    
    def next_frame(self):
        """
    Fetch the next frame in a sequence, given a set of internal
    read indexes.
    
    Internally updates / modifies:
        framebuffer
        _read_pointer
        _EOF
    
    Returns
    -------
    frame : np.ndarray
        Next sequential frame of data, with shape (framesize, channels)
        """
        if self.update_framebuffer():
            return np.array(self.framebuffer)
        
    
    def full_waveform(self, FORCE=False):
        """
    Read the entire waveform as a non-overlapping signal.
    
    Parameters
    ----------
    FORCE :  bool=False
        Over-ride the filesize safety check that prevents reading in too 
        much data into memory.
         
    Returns
    -------
    x : np.ndarray
        full signal read from the audiofile, bounded on [-1.0, 1.0)
        
        """
        if self.numsamples() < kMAX_FULL_WAVEFORM_LENGTH or FORCE:
            return self.read_frame_at_index(0, self.numsamples())
        else:
            raise ValueError("""Yikes! This file is longer than you might think ...
    Use 'FORCE=True' to over-ride this safety net.""")
    
    def spectrogram(self,N=None):
        """
    Compute the spectrogram of the initialized audiofile.
    
    Parameters
    ----------
    N : int=None
        optional N-length fft to compute
        
    Returns
    -------
    X : np.ndarray
        complex-valued spectrogram of the provided file
        
        """
        if N is None:
            N = self.framesize()
            
        K = N/2 + 1
        X = np.zeros([self.numframes(),K],dtype=np.complex)
        for m in range(self.numframes()):
            X[m] = rfft(self.next_frame().mean(axis=-1)*self.window.flatten(), N)

        self.reset()
        return X 
    
    def buffered(self):
        """
    Buffer the audiofile into a single matrix.
    
    Returns
    -------
    x : np.ndarray
        array of the audiofile, buffered with the provided framesize 
        and overlap parameters, with shape (M x framesize x channels) 
        
        """
        X = np.zeros([self.numframes(),self.framesize(),self.channels()])
        for m in range(self.numframes()):
            X[m] = self.next_frame()

        self.reset()
        return X


class CQT(FramedAudioFile):
    """
    """
    def __init__(self, filename, **kwargs):
        self.params = DEFAULT_CQT_PARAMS
        
        self.update_params(**kwargs)
        FramedAudioFile.__init__(self, filename = filename, **self.params)
        
        fmax=self.params.get('freq_max')
        Q=self.params.get('Q')
        bpo=self.params.get('bins_per_octave')
        octs = self.params.get('octaves')
        
        fmin = fmax*np.power(2.0,-octs)
        samplerate = float(np.power(2.0,np.ceil(np.log2(fmax*2))))
        self.A = cq_kernel2(q=Q,fmin=fmax/2.0,
                           octaves=1,
                           samplerate=samplerate,
                           bins_per_octave=bpo)
        self.update_params(freq_min=fmin,
                           framesize=(self.A.shape[1]-1)*2,
                           samplerate=samplerate)
        self._features = None
        self.audio_readers = [AudioReader(filename,
                                          framerate=self.framerate(),
                                          framesize=self.framesize(),
                                          samplerate=samplerate,
                                          framemode=self.framemode(),
                                          channels=self.channels(),
                                          verbose=self.verbose())]
        master_read_times = self.audio_readers[0].read_times()
        # For remaining octaves, create half-downsampled and insert at 0
        for _o in range(octs-1):
            next_fs = self.audio_readers[0].samplerate()/2.
            fname = self.audio_readers[0].wavefile()
            next_ar = AudioReader(fname,
                                     samplerate=next_fs,
                                     framesize=self.framesize(),
                                     read_times=master_read_times,
                                     framemode=self.framemode(),
                                     channels=self.channels(),
                                     verbose=self.verbose())
            self.audio_readers.insert(0,next_ar)
        return

    def spectra(self):
        """
        Compute the constant-Q spectra over a audio file.
        
        Returns
        -------
        cqspec : np.ndarray
            magnitude constant-Q spectra
        """
        
        speclist = [np.abs(np.dot(ar.spectrogram(),self.A.T)) for ar in self.audio_readers]
        
        n_len = min([xi.shape[0] for xi in speclist])
        X = np.concatenate([speclist[k][:n_len,:] for k in range(len(speclist))],axis=1)
        if self.params.get('log_coeff') > 0:
            X = np.log1p(self.params.get('log_coeff') * X) 
        return X
    
    def features(self):
        """
        Returns
        -------
        X : np.ndarray
            time-feature vector of this model.
        """
        if self._features is None:
            self._features = self.spectra()
        return self._features
    