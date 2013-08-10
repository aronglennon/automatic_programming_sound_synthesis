import random, sys, os
sys.path.append(os.curdir)
from max_connection import *
from javascript import fill_JS_file
from features.features_functions import get_features
import wave, copy

signal_generators = ["noise~", "cycle~", "saw~", "rand~", "sfplay~"]

class MaxPatch():
    def __init__ (self,rootObject,parentPatch,subPatch,connections,depth,count,fitness):
        self.root = rootObject
        self.parent = parentPatch
        self.children = subPatch
        self.connections = connections
        self.depth = depth
        self.count = count
        self.fitness = fitness    
    
    def patch_to_string(self):
        string = ''
        if self.root.name == 'dac~':
            string += '|dac~|'
        else:
            string += "|%s->%s" % (self.parent.root.name, self.root.name)
            if self.root.name == 'loadmess':
                string += "--%0.8f|" % (self.root.arguments[0]) 
            else:
                string += "|"
        for i in range(0,len(self.children)):
            if self.children[i] != []:
                string += self.children[i].patch_to_string()
            else:
                string += "|%s->dangling connection|" % (self.root.name)
        return string
    
    def start_max_processing(self, js_filename, wav_filename,feature_type, patch_type = 'processing'):
        # generate JS file
        fill_JS_file(js_filename, self, patch_type)
        # look for mfccs, when this file is populated, grab data and clear it out
        self.data = self.get_output(wav_filename, feature_type)
        # clear file contents - no need for wave.open here since we are just clearing out
        sample_features_file = open(wav_filename, 'w')
        sample_features_file.close()
    
    def get_output(self, filename, feature_type):
        # empty file is 48 bytes
        while os.path.getsize(filename) == 0:
            continue
        features = get_features(filename,feature_type)
        return features 
        
        

def create_patch_from_scratch(maxBranchLength, objectsToUse, init_type = "grow", max_resource_count = None):
    currentDepth = 0
    count = 0
    objects = objectsToUse
    # get dac~ as root
    currentDepth += 1
    count += 1
    dacPatch = MaxPatch(objects[0], None, [], [], currentDepth, count, 0.0)
    return create_patch(maxBranchLength, objects, dacPatch, dacPatch.depth, init_type, max_resource_count)

# used recursively to generate subpatches of size 1 and build from there
# note: cut inlets may be provided if a partial patch is sent in and only some inlets need to be filled out.
# an empty list for cut_inlets means this patch is 'pure' and therefore all inlets need to be treated.
# NOTE: max_resource_count is not strictly enforced, but once/if it is reached, terminals are added going forward
def create_patch(maxBranchLength, objectsToUse, patch, currentDepth, init_type = "grow", max_resource_count = None, cut_inlets = []):
    # disallow trivial situations
    if maxBranchLength <= 2:
        maxBranchLength = 3
    # if the patch's root has no inlets (i.e. is a terminal), we can't add on
    if patch.root.isTerminal:
        return
    for i in range(0,len(patch.root.inlets)):
        if cut_inlets != [] and i not in cut_inlets:
            continue
        connectionOutlet = 0
        connectionInlet = i
        # if we have hit our max, then we can only add on loadmess objects
        if maxBranchLength == currentDepth or max_resource_count is not None and max_resource_count <= 1:
            objectList = []
            for o in objectsToUse:
                if o.name == 'loadmess':
                    objectList.append(o)
            subpatchRoot = get_random_object_with_connection(objectList,patch.root.inlets[i].inletTypes)
        # if we are about to reach the max length or max resource count, make the root of the new subpatch patch a terminal...no matter what method we use
        elif maxBranchLength - currentDepth == 1 or max_resource_count is not None and max_resource_count <= 1:
            signalTerminalObjectList = []
            otherTerminalObjectList = []
            for o in objectsToUse:
                # store signal generator terminals in one list
                if o.name in signal_generators:
                    signalTerminalObjectList.append(o)
                # and non signal generator termianls in another
                elif o.isTerminal:
                    otherTerminalObjectList.append(o)
            # if we accept a signal, place a signal producer as a terminal
            if 'signal' in patch.root.inlets[i].inletTypes:
                subpatchRoot = get_random_object_with_connection(signalTerminalObjectList,patch.root.inlets[i].inletTypes)
            else:
                subpatchRoot = get_random_object_with_connection(otherTerminalObjectList,patch.root.inlets[i].inletTypes)
        # if the current root is a dac~, we must avoid the trivial situation by picking an object that is not a terminal...no matter what method we use
        elif currentDepth == 1 and patch.root.name == 'dac~':
            objectList = []
            for o in objectsToUse:
                if not o.isTerminal and o.name not in signal_generators:
                    objectList.append(o)
            subpatchRoot = get_random_object_with_connection(objectList,patch.root.inlets[i].inletTypes)
        # otherwise
        else:
            # if we use the grow method, select any object
            if init_type == "grow":
                subpatchRoot = get_random_object_with_connection(objectsToUse,patch.root.inlets[i].inletTypes)
            # if we use the full method and we are not at the max depth, pick a non-terminal
            elif init_type == "full":
                objectList = []
                for o in objectsToUse:
                    if not o.isTerminal and o.name not in signal_generators:
                        objectList.append(o)
                subpatchRoot = get_random_object_with_connection(objectList,patch.root.inlets[i].inletTypes)
                # in the case that there are no non-terminals to make a connection we must allow terminals to be used
                if subpatchRoot == []:
                    subpatchRoot = get_random_object_with_connection(objectsToUse,patch.root.inlets[i].inletTypes)
        if subpatchRoot == []:
            print 'bad logic'
        # if the loadmess maxobj, generate a random argument
        if subpatchRoot.name == 'loadmess':
            subpatchRoot.attach_random_argument(patch.root.inlets[i].lowVal, patch.root.inlets[i].highVal)
        subpatch = MaxPatch(subpatchRoot,None,[],[],1,1,0.0)
        if max_resource_count is not None:
            create_patch(maxBranchLength, objectsToUse, subpatch, currentDepth+1, init_type, max_resource_count-patch.count)
        else:
            create_patch(maxBranchLength, objectsToUse, subpatch, currentDepth+1, init_type)
        # if this inlet had a previous cut connection, replace the empty child
        if cut_inlets != []:
            patch.children[i] = subpatch
        else:
            patch.children.append(subpatch)
        patch.count += subpatch.count
        # some subpatches may be shallower than sibling subpatches
        if subpatch.depth >= patch.depth:
            patch.depth = subpatch.depth + 1
        subpatch.parent = patch
        # if the connection has been severed, just replace the empty connection
        if cut_inlets != []:
            patch.connections[i] = MaxConnection(connectionInlet, connectionOutlet, patch.root.inlets[i].inletTypes)
        else:
            patch.connections.append(MaxConnection(connectionInlet, connectionOutlet, patch.root.inlets[i].inletTypes))
    return patch

def get_random_object_with_connection(objects, requiredOutletTypes):
    objectsWithOutletType = []
    for i in range(0,len(objects)):
        for j in range(0, len(requiredOutletTypes)):
            if requiredOutletTypes[j] in objects[i].outlets:
                objectsWithOutletType.append(i)
    # necessary to make copies of objects in case the same types of objects get different arguments - e.g. loadmess
    if len(objectsWithOutletType) == 1:
        return copy.deepcopy(objects[objectsWithOutletType[0]])
    else:
        if len(objectsWithOutletType) == 0:
            return []
        return copy.deepcopy(objects[objectsWithOutletType[random.randint(0,len(objectsWithOutletType)-1)]])
