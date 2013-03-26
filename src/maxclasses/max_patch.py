import random, sys, os
sys.path.append(os.curdir)
from max_connection import *
from javascript import fill_JS_file
from features.features_functions import get_features
import wave, copy

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
            string += "|%s->%s|" % (self.parent.root.name, self.root.name)
        for i in range(0,len(self.children)):
            if self.children[i] != []:
                string += self.children[i].patch_to_string()
            else:
                string += "|%s->dangling connection|" % (self.root.name)
        return string
    
    def start_max_processing(self, filename,feature_type):
        # generate JS file
        fill_JS_file(self)
        # look for mfccs, when this file is populated, grab data and clear it out
        self.data = self.get_output(filename, feature_type)
        # clear file contents - no need for wave.open here since we are just clearing out
        sample_features_file = open(filename, 'w')
        sample_features_file.close()
    
    def get_output(self, filename, feature_type):
        while os.path.getsize(filename) == 0:
            continue
        sample_features_file = wave.open(filename, 'r')
        features = get_features(sample_features_file,feature_type)
        sample_features_file.close()
        return features 
        
        

def create_patch_from_scratch(maxBranchLength, objectsToUse, type = "full"):
    currentDepth = 0
    count = 0
    objects = objectsToUse
    # get dac~ as root
    currentDepth += 1
    count += 1
    dacPatch = MaxPatch(objects[0], None, [], [], currentDepth, count, 0.0)
    return create_patch(maxBranchLength, objects, dacPatch, dacPatch.depth, type)

# used recursively to generate subpatches of size 1 and build from there
# note: cut inlets may be provided if a partial patch is sent in and only some inlets need to be filled out.
# an empty list for cut_inlets means this patch is 'pure' and therefore all inlets need to be treated.
def create_patch(maxBranchLength, objectsToUse, patch, currentDepth, cut_inlets = [], type = "full"):
    # if the patch's root has no inlets (i.e. is a terminal), we can't add on
    if patch.root.isTerminal:
        return
    for i in range(0,len(patch.root.inlets)):
        if cut_inlets != [] and i not in cut_inlets:
            continue
        connectionOutlet = 0
        connectionInlet = i
        # if we are about to reach the max length, make the root of the new subpatch patch a terminal...no matter what method we use
        if maxBranchLength - currentDepth == 1:
            objectList = []
            for o in objectsToUse:
                if o.isTerminal:
                    objectList.append(o)
            subpatchRoot = get_random_object_with_connection(objectList,patch.root.inlets[i].inletTypes)
        # if the current root is a dac~, we must avoid the trivial situation by picking an object that is not a terminal...no matter what method we use
        elif currentDepth == 1 and patch.root.name == 'dac~':
            objectList = []
            for o in objectsToUse:
                if not o.isTerminal:
                    objectList.append(o)
            subpatchRoot = get_random_object_with_connection(objectList,patch.root.inlets[i].inletTypes)
        # otherwise
        else:
            # if we use the grow method, select any object
            if type == "grow":
                subpatchRoot = get_random_object_with_connection(objectsToUse,patch.root.inlets[i].inletTypes)
            # if we use the full method and we are not at the max depth, pick a non-terminal
            elif type == "full":
                objectList = []
                for o in objectsToUse:
                    if not o.isTerminal:
                        objectList.append(o)
                subpatchRoot = get_random_object_with_connection(objectList,patch.root.inlets[i].inletTypes)
        # if the loadmess maxobj, generate a random argument
        if subpatchRoot.name == 'loadmess':
            subpatchRoot.attach_random_argument(patch.root.inlets[i].lowVal, patch.root.inlets[i].highVal)
        subpatch = MaxPatch(subpatchRoot,None,[],[],1,1,0.0)
        create_patch(maxBranchLength, objectsToUse, subpatch, currentDepth+1)
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
        return copy.deepcopy(objects[objectsWithOutletType[random.randint(0,len(objectsWithOutletType)-1)]])



'''
// is the passed object in the vector?
bool isInMaxObjVector(const MaxObject& obj, std::vector<MaxObject>& maxObjs);

// select a random patch from a vector that hasn't already been used (specified by a vector of ints), then add index to the used vector
MaxPatch* selectRandomPatchFromVectorNotUsed(std::vector<MaxPatch>& patches, std::vector<int>& used);

// does the patch have a connection of the type specified?
bool hasConnection(MaxPatch* patch, std::string type);

// can the specified patch be severed anywhere so as to connect to the specified inlet
bool canConnect(MaxPatch* patch, const MaxInlet& inlet);

#endif
'''


'''
#include "MaxPatch.h"
#include <cstdlib>
#include <algorithm>
#include <string>

using namespace std;

// dummy default constructor
MaxPatch::MaxPatch()
{}

// this is actually recursive, because 'delete' calls the destructor first (which calls this) before doing normal cleanup
void MaxPatch::deletePatch()
{
    // for every child of this patch
    while (objects.size() != 0)
    {
        // delete the patch
        delete objects[0];
        // set the pointer to NULL (this is called after all of the recursions start to go back up, so at this point objects[0]
        // will have no children and setting it to NULL is the way to go)
        objects[0] = NULL;
        // erase the object from the vector, which makes the next object to delete the one at objects[0] again...
        objects.erase(objects.begin());
    }
    connections.erase(connections.begin(), connections.end());
}


// is the object compatible with the specified inlet? if not, return false. if so, return true and set typeOfCon to reflect
// the type of connection that makes the object compatible (if more than one, return a random type of those that are valid)
bool getCompatibleOutputAndType(MaxObject& maxObj, const MaxInlet& inlet, int outletWithCon, string& typeOfCon)
{
    // will hold all valid connections
    vector<int> validConnections; 
    // for every output connection (NOTE: as of now, only first is allowed anyway in the createPatch() method) and 
    // of the object and every inletType of the inlet)...
    for (int i = 0; i < maxObj.typeOfOutputConnections.size(); i++)
    {
        for (int j = 0; j < inlet.inletTypes.size(); j++)
        {
            // if the type of the output connection matches the inlet type of the inlet
            if (maxObj.typeOfOutputConnections[i] == inlet.inletTypes[j])
            {
                // ...mark this as a valid connection by saving the output connection number of the object
                // and inlet type number of the inlet as two-digit number 'ij'
                validConnections.push_back(i*10 + j);
            }
        }
    }
    // if there are no valid connections, return false
    if (validConnections.size() == 0) 
    {
        return false;
    }
    // ...otherwise
    else 
    {
        // choose a random valid connection
        int connection(validConnections[rand() % validConnections.size()]);
        // get the output associated with that connection
        outletWithCon = connection / 10;
        // set the type of connection to the type of the output connection
        typeOfCon = maxObj.typeOfOutputConnections[outletWithCon];
        // NOTE: we could also (and this might make more sense) find the inlet type that works
        // and use this to set typeOfCon. When/if more than one output is allowed, will this
        // make more sense?  Also, outletWithCon should be passed back too when more than one
        // outlet is allowed in createPatch() so that we can get the appropriate outlet for the 
        // connection
        return true;
    }
}

// Is the object in the object vector?
bool isInMaxObjVector(const MaxObject& obj, vector<MaxObject>& maxObjs)
{
    // set up a test variable
    string test;
    // for every object in the vector
    for (int i = 0; i < maxObjs.size(); i++)
    {
        // set test to be the current object name (from the object in the vector)
        test = maxObjs[i].name;
        // if the object in the vector has the same name as the object in question, return true
        if (test == obj.name)
        {
            return true;
        }
    }
    // if the specified object's name does NOT match any object's name in the vector, return false
    return false;
}

// Select a random patch from a vector of patches that has not already been selected (as specified in the
// used vector).
MaxPatch* selectRandomPatchFromVectorNotUsed(std::vector<MaxPatch>& patches, vector<int>& used)
{
    // choose a random patch from the patches vector
    int random;
    random = (rand() % patches.size());
    // if the random patch exists in the used vector, select another random patch
    while ( used.end() != find (used.begin(), used.end(), random) )
    {
        random = (rand() % patches.size());
    }
    // add the selected patch to the used vector
    used.push_back(random);
    // return the selected patch
    return &patches[random];
}

// does the specified patch have a connection of the specified type??? - recursive
bool hasConnection(MaxPatch* patch, std::string type)
{
    // for every output connection from the root
    for (int i = 0; i < patch->root->typeOfOutputConnections.size(); i++)
    {
        // if the connection is of the specified type, return true
        if (patch->root->typeOfOutputConnections[i] == type) 
        {
            return true;
        }
    }
    // for every subpatch
    for (int i = 0; i < patch->objects.size(); i++) 
    {
        // check to see if the subpatch has a connection of the specified type...if it does, return true
        if (hasConnection(patch->objects[i], type))
        {
            return true;
        }
    }
    // if neither this patch nor any of its subpatches have a connection of this type, return false
    return false;
}

// can the specified patch be severed anywhere so as to connect to the specified inlet - recursive
bool canConnect(MaxPatch* patch, const MaxInlet& inlet)
{
    // for every inlet type of the inlet
    for (int i = 0; i < inlet.inletTypes.size(); i++) 
    {
        // ...and for every output connection from the root
        for (int j = 0; j < patch->root->typeOfOutputConnections.size(); j++) 
        {
            // if the type of the output connection matches the type of the inlet, then the types are compatible
            // so return true
            if (patch->root->typeOfOutputConnections[j] == inlet.inletTypes[i])
            {
                return true;
            }
        }
    }
    // for every subpatch
    for (int i = 0; i < patch->objects.size(); i++) 
    {
        // check to see if any connections in the subpatch match one of the inlet's types.  if so, return true
        if (canConnect(patch->objects[i], inlet))
        {
            return true;
        }
    }
    // if neither the connections from the root, nor any of the connections in the subpatch's match an inlet type
    // return false
    return false;
}
'''
