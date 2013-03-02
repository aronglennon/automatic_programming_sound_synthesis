JS_FILE_NAME = '/etc/max/js_file.js'
AUDIO_SOURCE = 'sfplay~'

def fill_JS_file(patch):
    print 'filling JS File'
    js_file = open(JS_FILE_NAME, 'w')
    # Set the number of inlets and outlets
    js_file.write('inlets = 1;\n')
    js_file.write('outlets = 2;\n\n')
    # These are both necessary to make connections...the amnesia vector 'forgets' while the 'memory' one does not
    # ...see translateConnections for more
    memory = []
    amnesia = []
    
    # Make all Objects and Connections recursively by searching through tree
    objects = []
    #vector<string> objs;                // keeps track of all objects added in patch - used for labelling objects and when generating connections
    current_level = 0
    #int count(0);                        // used as current 'level' in patch when placing objects
    horizontal = [0,1]
    #vector<int> horizontal(1,0);        // keeps track of horizontal placement of each object through recursion - used when placing objects
    
    # Translate all objects in patch to javascript
    translate_objects(js_file, patch, current_level, objects, horizontal)
    # Translate all connections in patch to javascript
    translate_connections(js_file, patch, objects, memory, amnesia)
    
    # send a bang out of the object to start audio input through the patch
    js_file.write(" outlet(1, \"bang\");\n")
    
    # create eraseall function to be used right before next patch loads
    js_file.write("\nfunction eraseall()\n{\n")
    # this vector will hold the names of all objects to be deleted
    delete_objects = [];
    # Translate all object deletions to javascript
    translate_deletions(js_file, patch, delete_objects)
    js_file.write("}")

    # close connection to file
    js_file.close();

# *** RECURSIVE ***
def translate_objects(js_file,patch,current_level,objects,horizontal):
    # translate the root of this (sub)patch, unless it is a dac~ or sfplay~ because Max deals with them already
    if (patch.root.name != "dac~" and patch.root.name != "sfplay~"):
        name = convert_name(patch.root.name)
        objects.append(name)
        # find the number of objects with this name already in 'objects'
        same_objects = objects.count(name)
        '''
         create a new js object using the formatted js name for the object with its cardinality appened
         we also need to make sure we put this object in the appropriate place, which current_level and horizontal tell us
        '''
        # declare variable
        js_file.write('var obj%s%d;\n' % (name, same_objects))
        # set variable to a new patcher object with the appropriate real object name/identifier
        js_file.write('obj%s%d = this.patcher.newdefault(%d, %d,"%s"' % (name, same_objects, 300+(110*horizontal[current_level]),500 - 25*current_level, patch.root.name))
        # add any necessary arguments
        if patch.root.name == "loadmess":
            for a in patch.root.arguments:
                js_file.write(', %f' % a)
        # close off new patcher statement
        js_file.write(');\n\n')
    # increase the number of objects placed horizontally in current_level by one (b.c. we just put one there)
    horizontal[current_level] += 1
    # for each connection to root
    for i in range(0,len(patch.children)):
        # we are moving up one level
        current_level += 1
        # if this level has not been reached yet, our horizontal list will not be long enough, so add a 0
        if (len(horizontal) - 1) < current_level:
            horizontal.append(0)
        # now translate all objects that are part of the ith subpatch connected to our root
        translate_objects(js_file,patch.children[i], current_level, objects, horizontal)
        # when you come back down a level, decrease current_level
        current_level -= 1
      
def convert_name(object_name):
    name = object_name
    # if the root's name ends with a ~, cut it off b.c. js variable names can't have ~ in them
    if name[-1] == '~':
        name = object_name[:-1]
    # if the object is a math symbol, replace it with the written english equivalent
    if name == '+':
        name = 'add'
    elif name == '-':
        name = 'subtract'
    elif name == '/':
        name = 'divide'
    elif name == '*':
        name = 'multiply'
    return name

# *** RECURSIVE *** -----> must determine how amnesia and memory were SUPPOSED to work and go from there
def translate_connections(js_file,patch,objects,memory,amnesia):
    # transfer all objects in memory to the amnesia list
    amnesia = list(memory)
    # convert root name to js friendly name
    name = convert_name(patch.root.name)
    # place root name in both vectors
    amnesia.append(name)
    memory.append(name)
    # for every subpatch/child of the root
    for i in range(0,len(patch.children)):
        # first handle case where root is a dac~
        if patch.root.name == "dac~":
            # Tell thispatcher to name our object 'objdac' with 'i' appended (e.g. objdac4).
            # To get the appropriate object, we need to find the total number of object's with our name
            # and subtract the number of objects in the memory list (which is the number of object's up to this point
            # in the tree search), because objects are referred to by this patcher in the reverse order of creation
            js_file.write('outlet(0, "script", "nth", "objdac%d", "%s", %d);\n' % (i,patch.children[i].root.name,objects.count(convert_name(patch.children[i].root.name))-memory.count(convert_name(patch.children[i].root.name))))
            # Now that we've associated a variable name with this object, we can create its connection to the dac and its connection to the mfcc object (that which extracts features)
            js_file.write('outlet(0, "script", "connect", "objdac%d", %d, "dac", %d);\n' % (i,patch.connections[i].outlet, patch.connections[i].inlet))
            js_file.write('outlet(0, "script", "connect", "objdac%d", %d, "mfcc", 0);\n' % (i,patch.connections[i].outlet))
        # if the root is sfplay~
        elif patch.children[i].root.name == "sfplay~":
            # Tell thispatcher to name our object 'objadc' with 'i' appended. To get the appropriate object,
            # we find the total number of object's with our name and subtract the number we have found up to 
            # this part in the tree search and then add 1
            js_file.write('outlet(0, "script", "nth", "objadc%d", "%s", %d);\n' % (i,patch.root.name,objects.count(convert_name(patch.root.name))-memory.count(convert_name(patch.root.name))+1))
            # Now that we've associated a variable name with this object, we can create the appropriate connection out from sfplay~
            js_file.write('outlet(0, "script", "connect", "sfplay", %d, "objadc%d", %d);\n' % (patch.connections[i].outlet, i, patch.connections[i].inlet))
        # otherwise, simply make a connection based on the variable names created in the js file
        else:
            js_file.write('this.patcher.connect(obj%s%d, %d, obj%s%d, %d);\n\n' % (convert_name(patch.children[i].root.name), memory.count(convert_name(patch.children[i].root.name))+1,patch.connections[i].outlet, convert_name(patch.root.name), amnesia.count(convert_name(patch.root.name)),patch.connections[i].inlet))
        # translate connections for every subpatch
        translate_connections(js_file, patch.children[i], objects, memory, amnesia)


def translate_deletions(js_file, patch, objects):
    # leave alone default audio in and out objects, because we don't want to ever delete these
    if patch.root.name != "dac~" and patch.root.name != "sfplay~":
        # convert the name to a js friendly one
        name = convert_name(patch.root.name)
        # add this object to the object names list
        objects.append(name)
        # find out how many objects that exist in the list already have this name
        same_objects = objects.count(name)
        
        # tell js file to remove an object with this name
        js_file.write(' this.patcher.remove(obj%s%d);\n' % (name, same_objects))
    # for every subpatch connected to our root, delete all of its objects
    for i in range(0,len(patch.children)):
        translate_deletions(js_file, patch.children[i], objects)