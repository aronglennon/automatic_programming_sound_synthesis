from max_inlet import *
import random

class MaxObject():
    def __init__ (self,name,inlets,outlets,arguments=[],isRoot=False,isTerminal=False):
        self.name = name
        self.inlets = inlets # contains MaxInlet objects
        self.outlets = outlets # just needs to contain outlet types
        self.arguments = arguments
        self.isTerminal = isTerminal
        self.isRoot = isRoot
    
    def selectRandomOutlet(self,connectionType):
        print ''
    
    def selectInletsRandomType(self,inlet):
        print ''
    
    def attach_random_argument(self,lowValue,highValue):
        rawRandom = random.random()
        self.arguments.append(rawRandom*(highValue-lowValue) + lowValue)
        
def get_max_objects_from_file(object_list_file):
    objectList = []
    # TODO: Look into tree data structure in python
    all_text = object_list_file.read()
    objects = all_text.split('\n')
    for o in objects:
        isRoot = False
        isTerminal = False
        name = o.split('|')[0]
        print name
        insAndOuts = o.split('|')[1]
        inlets = []
        outlets = []
        ins = insAndOuts.split('/')[0]
        outs = insAndOuts.split('/')[1]
        if len(ins) == 0:
            print 'no inputs'
            isTerminal = True
        else:
            inList = ins.split('\'')
            for inlet in inList:
                intype = inlet.split(':')[0]
                # see if inlet can accept multiple types
                if len(intype.split(' ')) > 1:
                    intype = intype.split(' ')
                else:
                    intype = [intype]
                low = float(inlet.split(':')[1])
                high = float(inlet.split(':')[2])
                inlets.append(MaxInlet(intype,high,low))
        if len(outs) == 0:
            print 'no outputs'
            isRoot = True
        else:
            outlets = outs.split(' ')
        objectList.append(MaxObject(name,inlets,outlets,isRoot=isRoot,isTerminal=isTerminal))
    return objectList