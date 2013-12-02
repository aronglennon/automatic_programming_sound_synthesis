'''
Created on May 24, 2013

@author: ejhumphrey
'''

import cPickle
import numpy as np
import theano
import theano.tensor as T

from acousim import DEFAULT_PARAMS
from acousim.core import ParamObject, Conv3DArgs, AffineArgs, Network
from acousim.timefreq import CQT

DEFAULT_ARCH = [Conv3DArgs(input_shape=(1,5,168),weight_shape=(30,3,25),pool_shape=(1,4)),   #3x36
               Conv3DArgs(weight_shape=(50,3,15),pool_shape=(1,2)),     #1x11                      
               AffineArgs(output_shape=(200,)),     #550->200
               AffineArgs(output_shape=(50,)),
               AffineArgs(output_shape=(8,))]

class Transform(ParamObject):
    
    def __init__(self, graph, **kwargs):
        ParamObject.__init__(self, **kwargs)
        self.graph = graph
        self.compile_functions()
        
    def graph_io(self):
        """
        Stock implementation assumes single input, single output
        Subclass for more interesting behavior ...
        
        Returns
        -------
        tuple, inputs as a list, output as a variable 
        """
        
        # Create symbolic ins and outs
        # Might not need to make this a class member
        x_in = self.graph.symbolic_input('x_in')
        z_out = self.graph.transform_fwd(x_in)
        return [x_in],z_out
    
    def compile_functions(self):
        """
        produces three stock functions:
            fx_loss() : compute the loss given the appropriate inputs
            fx_update() : same as above, while modifying the graph's
                parameters in place.
            fx_output() : compute the graph's output given an input
        
        certain cases may warrant extending ... should only need to 
        call superclass's method AND write additional function calls 
        """
        
        graph_input, graph_output = self.graph_io()
        self.fx_output = theano.function(inputs=graph_input,
                                            outputs=graph_output,
                                            allow_input_downcast=True)
        return
    
def _load_fx(param_file=DEFAULT_PARAMS,
             arch=DEFAULT_ARCH):
    
    nnet = Transform(graph=Network(arch))
    pvs = cPickle.load(open(param_file,'r'))
    nnet.graph.set_param_values(pvs)
    return nnet.fx_output

_fx_proj = _load_fx()

def shingle(x,L,hopsize):
    """
    tiling
    x : matrix
    L : number of adjacent frames to concatenate
    """
    N,D = x.shape
    M = (N - L)/hopsize + 1
    idx = hopsize*np.arange(M)[:,np.newaxis]+np.arange(L)
    return x[idx]

def timbrespace(sndfile, hopsize=3):
    """
    Parameters
    ----------
    sndfile : str
        filepath to sound file to parse
    hopsize : int
        frames between observations, based on a 20Hz framerate. i.e. a 
        hopsize of 2 corresponds to 0.10 seconds. stay at/below 5 (no overlap)
    
    Returns
    -------
    coords : np.ndarray
        timbre-space coordinates, with shape (N,3), where N is a function of
        the input file duration
        
    """
    cq = CQT(filename=sndfile)
    X = cq.features()
    Xs = shingle(X, L=5, hopsize=hopsize)
    if Xs.ndim==3:
        Xs = Xs[:,np.newaxis,...]
    return _fx_proj(Xs)






