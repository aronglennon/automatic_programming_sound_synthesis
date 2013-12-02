'''
Created on May 24, 2013

@author: ejhumphrey
'''

import theano
import theano.tensor as T
import numpy as np
from theano.tensor.shared_randomstreams import RandomStreams
from theano.tensor.signal import downsample, conv

FLOATX = 'float32'

class ParamObject():
    def __init__(self, **kwargs):
        self._params = {}
        self._params.update(**kwargs)
        
        
# - Layer Classes ---
def gen_layer(layer_args):
    """
    dumb look-up for a given LayerArg obj
    
    Good god, this is dangerous.
    """
    
    return eval(layer_args.type.split("Args")[0])(layer_args)

# -- LayerArgs --- 
class BaseLayerArgs(ParamObject):
    """
    Base class for all layer arguments
    """
    def __init__(self, **kwargs):
        """
    input_shape : tuple
        shape of input array, regardless of batch size
    output_shape : tuple
        shape of transformed output
    act_fwd : function
        Forward transform non-linearity
    act_inv : function
        Inverse transform non-linearity
    direction : str
        one of ['both','fwd','inv']
    num_repetitions : int
        number of times to apply the layer
    param_values : dict
        parameter name and np.ndarray parameters
    layer_name : str
        for aesthetic convenience, helps debugging
    
        """
        ParamObject.__init__(self, **kwargs)
    
        self.type = self.__class__.__name__
        self._params = {'input_shape':(),
                       'output_shape':(),
                       'act_fwd':T.tanh,
                       'act_inv':T.tanh,
                       'direction':'both',
                       'param_values':None,
                       'layer_name':"?",
                       'dropout':False,
                       'num_repetitions':1}
        
        self.update(**kwargs)
        # Forward Transform non-linearity
        self.act_fwd = self.get('act_fwd')
        # Inverse Transform non-linearity
        self.act_inv = self.get('act_inv')
    
    def num_repetitions(self):
        return self.get('num_repetitions')
    
    def input_shape(self):
        """
    Returns
    -------
    shp : tuple
        
        """
        return self.get('input_shape')
    
    def output_shape(self):
        """
    Returns
    -------
    shp : tuple
        
        """
        return self.get('output_shape')
    
    def update(self, **kwargs):
        for k in kwargs:
            if not k in self._params:
                raise ValueError("Uncaught keyword: '%s'"%k)
        
        self._params.update(**kwargs) 
    
    def get(self, k):
        return self._params.get(k)
    
class AffineArgs(BaseLayerArgs):
    """
    """
    
    def __init__(self, **kwargs):
        """
    Parameters
    ----------
    Defining shapes, in order or precedence
    1. param_values : list / tuple of np.ndarrays
        packed list, returned by layer.param_values()
    
    2. weight_shape : tuple
        forward weight shape (n_in, n_out)
    
    3. output_shape : tuple
        (n_out,) shape of transformed output
        
    act_fwd : function
        Forward transform non-linearity
    act_inv : function
        Inverse transform non-linearity
    direction : str
        one of ['both','fwd','inv']
    param_values : dict
        parameter name and np.ndarray parameters
    layer_name : str
        for aesthetic convenience, helps debugging
    
    
    Note: for sanity's sake, Affine Layers will reshape all 
    math to 2D-matrix operations.
    
        """
        _my_params = {'weight_shape':(),
                      'flatten':2,
                      'bias':True}
        
        #kwarg check...
        assert sum(['param_values' in kwargs,
                    'weight_shape' in kwargs,
                    'output_shape' in kwargs]) == 1
              
        
        for k in _my_params:
            _my_params[k] = kwargs.pop(k,_my_params[k])
            
        BaseLayerArgs.__init__(self, **kwargs)
        self._params.update(**_my_params)
        
        if len(_my_params.get('weight_shape'))==2:
            self.update(weight_shape = _my_params.get('weight_shape'))
        
        
    def update(self, **kwargs):
        BaseLayerArgs.update(self, **kwargs)
        if 'weight_shape' in kwargs:
            n_in, n_out = kwargs.get('weight_shape')
            self._params.update(input_shape = (n_in,),
                                output_shape = (n_out,))
        elif 'input_shape' in kwargs:
            self._params.update(input_shape=(np.prod(kwargs['input_shape']),))
            self._params.update(weight_shape=(self.input_shape()[0],
                                              self.output_shape()[0]))

    def weight_shape(self, direction='fwd'):
        s = self.get('weight_shape')
        if direction == 'fwd':
            return s
        elif direction == 'inv':
            return (s[1], s[0])

class Conv3DArgs(BaseLayerArgs):
    
    def __init__(self, **kwargs):
        """
    Note that input_shape *does not* need to be specified, and can
    be determined dynamically later. However, this must be explicitly
    performed in the managing graph.
        
    param_values : list / tuple of np.ndarrays
        packed list, returned by layer.param_values()
    
    --- OR ---
    
    input_shape : tuple
        (in_maps, in_dim0, in_dim1), the last three dims of a 4d tensor
        with a typical shape (n_points, nmaps, dim0, dim1)
    weight_shape : tuple
        (out_maps, dim0, dim1)
    
    pool_shape : tuple
        (dim0, dim1)
    downsample_shape : tuple
        (dim0, dim1)
    act_fwd : function
        Forward transform non-linearity
    act_inv : function
        Inverse transform non-linearity
    
    
        """
        
        _my_params = {'weight_shape':(),
                      'pool_shape':(1,1)}
        
        for k in _my_params:
            _my_params[k] = kwargs.pop(k,_my_params[k])
        
        
        BaseLayerArgs.__init__(self, **kwargs)
        self._params.update(**_my_params)
        
        if not self.get('param_values') is None:
            self.update(weight_shape = self.get('param_values')[0].shape)
        
        elif len(self.get('input_shape')) > 0:
            self.update(input_shape = self.get('input_shape'))
    
    def update(self, **kwargs):
        BaseLayerArgs.update(self, **kwargs)
        if self.get('weight_shape') is None:
            return 
        
        # adjust weight_shape?
        if 'input_shape' in kwargs:
            w = list(self.get('weight_shape'))
            if len(w)==3:
                w.insert(1, self.input_shape()[0])
            elif len(w)==4:
                w[1] = self.input_shape()[0]
            else:
                raise ValueError("len(weight_shape) must equal 3 or 4")
            self._params.update(weight_shape = tuple(w))
            
        # recompute output shape?
        if True in [k in kwargs for k in ['weight_shape','pool_shape','input_shape']]:
            d0_out = (self.input_shape()[1] - self.weight_shape()[-2] + 1) / self.pool_shape()[0]
            d1_out = (self.input_shape()[2] - self.weight_shape()[-1] + 1) / self.pool_shape()[1]
            self._params.update(output_shape = (self.weight_shape()[0], d0_out, d1_out))
            
        elif 'input_shape' in kwargs:
            self._params.update(input_shape=(np.prod(kwargs['input_shape']),))
            self._params.update(weight_shape=(self.input_shape()[0],
                                              self.output_shape()[0]))

    
    def pool_shape(self):
        return self.get('pool_shape')
    
    def weight_shape(self, direction='fwd'):
        s = self.get('weight_shape')
        if direction=='fwd':
            return s
        elif direction=='inv':
            return (s[1], s[0], s[2], s[3])
        
        
# -- Layer Implementations ---
class BaseLayer(object):
    
    """
    Layers are in charge of parameter management and micro-math operations.
    """
    
    def __init__(self, layer_args):
        """
        Takes a layer_arg object
        """
        
        self.type = self.__class__.__name__
        self.args = layer_args
        
        # alias locally
        self.numpy_rng = np.random.RandomState()
        self.theano_rng = RandomStreams(self.numpy_rng.randint(2 ** 30))
        
        self.act_fwd = self.args.get('act_fwd')
        self.act_inv = self.args.get('act_inv')
        
        self.dropout_prob = theano.shared(0.0, allow_downcast=True)
        self.dropout_scalar = theano.shared(0.5, allow_downcast=True)
        self.set_dropout(self.args.get('dropout'))
        
        # Theta is the dictionary of all symbolic parameters in this layer.
        # However, to prevent terrible, terrible things, use self.params(), which
        # takes a str argument for which params to return
        #
        # IMPORTANT: the parameter names must contain '_fwd' or '_inv' to be collected
        #            appropriately.
        
        self._theta = {}
        
        # TODO: Something to think about ... why not just make this easier and
        #       maintain two separate networks ... whatever, for now. 
        
                
    def set_param_values(self, param_dict):
        """
    Parameters
    ----------
    param_dict : dict
        key/value pairs of parameter name and np.ndarray
            
        """
        for k,v in param_dict.items():
            if not k in self._theta:
                # Catch unexpected parameter names
                raise ValueError("Unexpected parameter name: %s"%k)
            elif self._theta[k] is None:
                # If properly declared, but uninitialized, do so now 
                self._theta[k] = theano.shared(value=v.astype(FLOATX),
                                               name=k +' (%s)'%self.layer_name())
            else:
                # And set value of shared type
                self._theta[k].set_value(v.astype(FLOATX))
            
    def params(self, direction):
        """
    return the symbolic parameters of the layer corresponding to a given direction.
        
    Parameters
    ----------
    direction : str
        one of ['both','fwd','inv']
    
    Returns
    -------
    params : dict
        symbolic parameters of the layer, keyed by name
        
        """
        
        if direction == 'both':
            param_names = self._theta.keys()
        else:
            param_names = []
            for k in self._theta:
                if k.count('_'+direction)>0:
                    param_names += [k] 
        
        params = {}
        for k in param_names:
            params[k] = self._theta[k]
        
        return params
    
    
    def param_values(self, direction):
        """
    return the numeric parameters of the layer corresponding to a given direction.
    
    Parameters
    ----------
    direction : str
        one of ['both','fwd','inv']    
    
    Returns
    -------
    vals : dict
        np.ndarray values of the layer; necessary for saving in case of
        future upgrades and whatnot.
        
        """
        params = self.params(direction)
        param_values = {}
        for k in params:
            param_values[k] = params[k].get_value() 
            
        return param_values
        
    def input_shape(self):
        """
    Returns
    -------
    shp : tuple
    
    Think about pulling this from the parameters...    
        """
        return self.args.input_shape()
    
    def output_shape(self):
        """
    Returns
    -------
    shp : tuple
    
    Think about pulling this from the parameters...    
        """
        return self.args.output_shape()
    
    def transform_fwd(self, x_in):
        """
    x_input : symbolic theano variable
        
        """
        raise NotImplementedError("Subclass me!")
    
    def transform_inv(self, z_in):
        """
    z_input : symbolic theano variable
        
        """
        raise NotImplementedError("Subclass me!")
    
    def layer_name(self):
        return self.args.get('layer_name')
    
    def set_dropout(self, toggle):
        """
        toggle : bool
            turn dropout on or off
        """
        self.dropout=toggle
        
        self.dropout_prob.set_value(0.5 if self.dropout else 0.0)
        # if dropout is off, we need to halve the weights
        self.dropout_scalar.set_value(1.0 if self.dropout else 0.5)
    
class Affine(BaseLayer):
    
    """
    Affine Transform Layer
      (i.e., a fully-connected non-linear projection)
      
    
    """
    
    def __init__(self, layer_args):
        """
        layer_args : AffineArgs
            
        """
        BaseLayer.__init__(self, layer_args)
        self._theta = {'W_fwd':None, 'W_inv':None,}
        
        if self.args.get('bias'):
            self._theta.update({'b_fwd':None,'b_inv':None,})
        
        # Two matrices
        if not self.args.get('param_values') is None:
            self.set_param_values(self.args.get('param_values'))
        else:
            # Create all the weight values at once
            W_shp = tuple([2] + list(self.args.weight_shape()))
            W_vals = np.asarray(self.numpy_rng.normal(loc=0.0,
                                                      scale=np.sqrt(6. / np.sum(self.args.weight_shape())),
                                                      size=W_shp), dtype=FLOATX)
            b_vals = [np.zeros(self.output_shape()), np.zeros(self.input_shape())]
            
            self.set_param_values({'W_fwd':W_vals[0],
                                   'W_inv':W_vals[1].T,})
            if self.args.get('bias'):
                self.set_param_values({'b_fwd':b_vals[0],'b_inv':b_vals[1],})
            
    
    def transform_fwd(self, x_in):
        """
        will fix input tensors to be matrices as the following:
        (N x d0 x d1 x ... dn) -> (N x prod(d_(0:n)))
        
        Dropout should go here...
        
        """
        
        W = self._theta['W_fwd']
        b = self._theta['b_fwd'].dimshuffle('x',0) if self.args.get('bias') else 0.0
        x_in = T.flatten(x_in, outdim=self.args.get('flatten'))
        if self.args.get('flatten')==1:
            x_in = x_in.dimshuffle('x',0)
        
        selector = self.theano_rng.binomial(size=self.args.input_shape(), 
                                            p=1.0-self.dropout_prob,
                                            dtype=FLOATX)
        W = W*selector.dimshuffle(0,'x')*self.dropout_scalar
        return self.act_fwd(T.dot(x_in, W) + b) 
        
    def transform_inv(self, z_in):
        """
        will fix input tensors to be matrices as the following:
        (N x d0 x d1 x ... dn) -> (N x prod(d_(0:n)))
        """
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        # TODO: There *will* be problems for networks that required
        #        flattening the input. Need to fix this.
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        W = self._theta['W_inv']
        b = self._theta['b_inv']
         
        return self.act_inv(T.dot(z_in, W) + b.dimshuffle('x',0))
    
class Conv3D(BaseLayer):
    
    """
      
    
    """
    
    def __init__(self, layer_args):
        """
        layer_args : ConvArgs
            
        """
        BaseLayer.__init__(self, layer_args)
        
        self._theta = {'W_fwd':None,'b_fwd':None,
                       'W_inv':None,'b_inv':None,}
        
        if not self.args.get('param_values') is None:
            self.set_param_values(self.args.get('param_values'))
       
        else:
            # Create all the weight values at once
            fan_in = np.prod(self.args.weight_shape('fwd')[1:])
            W_fwd = np.asarray(self.numpy_rng.normal(loc=0.0,
                                                      scale=np.sqrt(3. / fan_in),
                                                      size = self.args.weight_shape('fwd')), dtype=FLOATX)
#            W_fwd = np.asarray(self.numpy_rng.uniform(low = -np.sqrt(3. / fan_in),
#                                                      high = np.sqrt(3. / fan_in),
#                                                      size = self.args.weight_shape('fwd')),
#                                                      dtype = FLOATX)
            if self.act_fwd == T.nnet.sigmoid:
                W_fwd *= 4
            b_fwd = np.zeros(self.args.weight_shape('fwd')[0])
            
            fan_in = np.prod(self.args.weight_shape('inv')[1:])
            W_inv = np.asarray(self.numpy_rng.uniform(low = -np.sqrt(3. / fan_in),
                                                      high = np.sqrt(3. / fan_in),
                                                      size = self.args.weight_shape('inv')),
                                                      dtype = FLOATX)
            
            if self.act_inv == T.nnet.sigmoid:
                W_inv *= 4
            b_inv = np.zeros(self.args.weight_shape('inv')[0])
            self.set_param_values({'W_fwd':W_fwd,
                                   'W_inv':W_inv,
                                   'b_fwd':b_fwd,
                                   'b_inv':b_inv,})
        
#        self.dropout_scalar = theano.shared(cast(1.0,dtype=FLOATX), allow_downcast=True, broadcastable=(True,True,True,True))
    
    def transform_fwd(self, x_in):
        """
        
        """
        W = self._theta['W_fwd']
        b = self._theta['b_fwd']
        
#        W = W*selector.dimshuffle(0,'x','x','x')/scalar
        
        z_out = T.nnet.conv.conv2d(input=x_in,
                                   filters=W,
                                   filter_shape=self.args.weight_shape('fwd'),
                                   border_mode='valid')
        
        
        selector = self.theano_rng.binomial(size=self.output_shape()[:1], p=1-self.dropout, dtype=FLOATX)
#        scalar = selector.sum()
        scalar = 1.0# self.dropout_scalar
        
        z_out = (z_out + b.dimshuffle('x', 0, 'x', 'x'))*selector.dimshuffle('x',0,'x','x')*scalar
        z_out = self.act_fwd(z_out)
        return downsample.max_pool_2d(z_out,self.args.pool_shape(),ignore_border=False)
    
    def transform_inv(self, z_in):
        """
        This is going to die for anything other than pool_shape==(1,1)
        """
        W = self._theta['W_inv']
        b = self._theta['b_inv']
        
        d1,d2,d3 = self.args.output_shape()
        z_in = T.reshape(z_in, newshape=(z_in.shape[0],d1,d2,d3), ndim=4)
        
        x_out = T.nnet.conv.conv2d(input=z_in,
                                   filters=W,
                                   filter_shape=self.args.weight_shape('inv'),
                                   border_mode='full')
        x_out = self.act_inv(x_out + b.dimshuffle('x', 0, 'x', 'x'))
        
        return x_out
    
# - Network Class ---
class Network(object):
    
    """
    Non-recursive 
    """    
    def __init__(self, layer_args):
        """
        layer_args : list
            layer argument objects corresponding to the network to build.
        
        """
        # Important! add_layer manages the internal architecture list
        self.layers = []    # Layers
        self.arch = []      # LayerArgs
        
        # Iterate over the args passed to init
        [self.add_layer(largs) for largs in layer_args]
    
    def symbolic_input(self, name):
        """
        Return a symbolic theano variable fitting this network
        
        Parameters
        ----------
        name : str
            string for the variable. must be unique to calling entity,
            because it will be live for subsequent function calls.
        """
        n_dim = len(self.input_shape())
        if n_dim == 1:
            x_in = T.matrix(name=name, dtype=FLOATX)
        elif n_dim == 2:
            x_in = T.tensor3(name=name, dtype=FLOATX)
        elif n_dim == 3:
            x_in = T.tensor4(name=name, dtype=FLOATX)
        else:
            raise ValueError("Unsupported input dimensionality: %d"%n_dim)
        
        return x_in
    
    def symbolic_output(self, name):
        """
        Return a symbolic theano variable fitting this network
        
        Parameters
        ----------
        name : str
            string for the variable. must be unique to calling entity,
            because it will be live for subsequent function calls.
        """
        n_dim = len(self.output_shape())
        if n_dim == 1:
            x_in = T.matrix(name=name, dtype=FLOATX)
        elif n_dim == 2:
            x_in = T.tensor3(name=name, dtype=FLOATX)
        elif n_dim == 3:
            x_in = T.tensor4(name=name, dtype=FLOATX)
        else:
            raise ValueError("Unsupported input dimensionality: %d"%n_dim)
        
        return x_in
    
    def add_layer(self, layer_args):
        """
        layer_args : LayerArg object
            
            
        if any info is missing from the layer_args regarding shape,
        try to infer it from the previous layer.
        """
        
        layer_args.update(layer_name=len(self.arch))
        if len(layer_args.input_shape())==0:
            # If input_shape is undefined, attempt to recover
            #   from the output of the previous layer...
            layer_args.update(input_shape = self.arch[-1].output_shape())
        
        self.arch += [layer_args]
        self.layers += [gen_layer(layer_args)]
        
    def model(self):
        """
        I think this is supposed to zip up everything you would need
        to pass to a new graph ... 
        """
        model_list = []
        for args,layer in zip(self.arch, self.layers):
            args.update(param_values = layer.param_values())
            model_list += [args]
        return model_list
    
    def params(self, layer_idx=None, direction='both'):
        """
        Collect symbolic parameters in a nested dictionary
        
        Parameters
        ----------
        layer_idx responds to the following
        = None
            returns the symbolic parameters for all layers
        ints : array_like
            returns the layers indexed by the given integers,
            NB: len(layer_idx) <= len(self.layers)
        bool : array_like
            returns the layers based on the truth values,
            NB: len(layers) == len(self.layers)
            
        direction : str
            catches one of the following ['both','fwd','inv']
            
        Returns
        -------
        params : dict of dicts
            top level keys are layer ints, second level are param names
            
        """
            
        idxs = np.arange(len(self.layers),dtype=int)
        if layer_idx is None:
            # If absent, take them all
            layer_idx = idxs
        else:
            # If either ints or bools, make them ints
            layer_idx = np.asarray([layer_idx]).flatten()
            layer_idx = idxs[layer_idx]
        
        params = {}
        for i in layer_idx:
            params[i] = self.layers[i].params(direction=direction)
            
        return params
    
    def param_values(self, layer_idx=None, direction='both'):
        """
        Collect numerical parameters in a nested dictionary
        
        Parameters
        ----------
        layer_idx responds to the following
        = None
            returns the symbolic parameters for all layers
        ints : array_like
            returns the layers indexed by the given integers,
            NB: len(layer_idx) <= len(self.layers)
        bool : array_like
            returns the layers based on the truth values,
            NB: len(layers) == len(self.layers)
            
        direction : str
            catches one of the following ['both','fwd','inv']
            
        Returns
        -------
        param_valuess : dict of dicts
            top level keys are layer ints, second level are param names
        
        """
        params = self.params(layer_idx, direction)
        param_values = {}
        for ki in params:
            param_values[ki] = {}
            for pname in params[ki]:
                param_values[ki][pname] = params[ki][pname].get_value()
        
        return param_values
    
    def set_param_values(self, param_values):
        """
        Parameters
        ----------
        param_values : dict of dicts
            nested dictionary of numerical parameter values. Top
            level keys are integers corresponding to the layer index,
            second level keys reference the parameter name.
        """
        [self.layers[i].set_param_values(param_values[i]) for i in param_values]
        
    def dropout(self):
        """
        collect dropout bools over the graph
        
        Returns
        -------
        bool_list : list
            take a wild guess
        """
        return [l.dropout for l in self.layers]
    
    def set_dropout(self, bool_list):
        """
        set dropout bools over the graph
        """
        [l.set_dropout(b) for l,b in zip(self.layers,bool_list)]

    def transform_fwd(self, x_in):
        """
    Forward transform an input through the network
    
    Parameters
    ----------
    x_in : theano symbolic type
        we're not doing any checking, so it'll die if it's not correct
    
    Returns
    -------
    z_out : theano symbolic type
        
        """
        layer_input = x_in
        for l in range(len(self.layers)):
            for reps in range(self.layers[l].args.num_repetitions()):
                layer_input = self.layers[l].transform_fwd(layer_input)
        
        return layer_input
    
    def transform_inv(self, z_in):
        """
    Inverse transform an output through the network
    
    Parameters
    ----------
    z_in : theano symbolic type
        we're not doing any checking, so it'll die if it's not correct
    
    Returns
    -------
    x_rec : theano symbolic type
        a (hopefully) reconstructed input
        """
        layer_input = z_in
        # reshaping goes here
        for l in range(len(self.layers))[::-1]:
            layer_input = self.layers[l].transform_inv(layer_input)
            # reshaping goes here
        
        return layer_input
    
    def input_shape(self):
        return self.arch[0].input_shape()
    
    def output_shape(self):
        return self.arch[-1].output_shape()
    