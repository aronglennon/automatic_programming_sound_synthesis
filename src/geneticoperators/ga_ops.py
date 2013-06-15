import random
import copy
from maxclasses.max_patch import create_patch
import numpy as np
from geneticoperators.fitness import change_fitness_to_probability

TOURNAMENT_SIZE = 7
PARSIMONY_PROB = 0.7
PARSIMONY_TOURNAMENT_SIZE = 2

def select_patches(patches, selection_type):
    selected_patches = []
    if selection_type == 'fitness-proportionate':
        # perform fitness proportionate selection
        change_fitness_to_probability(patches, 'proportionate', 'high')                # "low" tells the function that a lower score is considered better and "high" means higher is better
        cum_sum = [patches[0].fitness]
        for p in patches[1:]:
            # add the last cum_sum value to the next fitness value to get the next cum_sum value
            cum_sum.append(p.fitness+cum_sum[-1])
        for p in patches:
            rand_num = random.random()
            # find the first item index in cum_sum where the value is greater than the rand_num
            itemindex = np.where(np.asarray(cum_sum)>rand_num)[0][0]
            # the sum may be to a fraction less than 1.0, so just in case we happen to pick that random number, we just set the value to the last index
            if itemindex == -1:
                itemindex = len(patches)-1
            selected_patches.append(copy.deepcopy(patches[itemindex]))
    elif selection_type == 'ranking-selection':
        change_fitness_to_probability(patches, 'ranking', 'high')
        cum_sum = [patches[0].fitness]
        for p in patches[1:]:
            # add the last cum_sum value to the next fitness value to get the next cum_sum value
            cum_sum.append(p.fitness+cum_sum[-1])
        for p in patches:
            rand_num = random.random()
            # find the first item index in cum_sum where the value is greater than the rand_num
            itemindex = np.where(np.asarray(cum_sum)>rand_num)[0][0]
            # the sum may be to a fraction less than 1.0, so just in case we happen to pick that random number, we just set the value to the last index
            if itemindex == -1:
                itemindex = len(patches)-1
            selected_patches.append(copy.deepcopy(patches[itemindex]))
    elif selection_type == 'tournament-selection':
        for p in patches:
            # choose a random subset of patches - the first one will be the one with highest fitness
            index_list = random.sample(xrange(len(patches)), TOURNAMENT_SIZE)
            selected_patches.append(copy.deepcopy(patches[index_list[0]]))
    elif selection_type == 'double-tournament-selection':
        for p in patches:
            # run TOURNAMENT_SIZE parsimony tournaments
            parsimony_winner_patches = []
            for i in range(0, TOURNAMENT_SIZE):
                index_list = random.sample(xrange(len(patches)), PARSIMONY_TOURNAMENT_SIZE)
                most_parsimonious_patch = patches[index_list[0]]
                for i in index_list:
                    if patches[i].count < most_parsimonious_patch.count:
                        most_parsimonious_patch = patches[i].count
                random_num = random.random()
                if random_num < PARSIMONY_PROB:
                    parsimony_winner_patches.append(copy.deepcopy(most_parsimonious_patch))
                else:
                    # (1 - PARSIMONY_PROB) of the time just select a patch we would have chosen randomly
                    index = random.randint(0, len(index_list)-1)
                    parsimony_winner_patches.append(copy.deepcopy(patches[index_list[index]]))
            # sort the parsimony winner patches by fitness and choose the best one
            parsimony_winner_patches.sort(key = lambda x:x.fitness, reverse = True)
            selected_patches.append(parsimony_winner_patches[0])
    return selected_patches
        
def split_selected_into_gen_ops(selected, gen_ops):
    print 'return a set of patches for use in crossover and a set for use in mutation based on probabilities'
    gen_probs = [0]
    gen_ops_patches = []
    # create cumulative prob list and fill gen_ops_patches with gen op names
    for i in range(0, len(gen_ops)):
        gen_probs.append(gen_ops[i][1]+gen_probs[i])
        gen_ops_patches.append([gen_ops[i][0]])
    gen_ops_patches = dict.fromkeys(gen_ops_patches, [])
    # go through all but last selected patch and just assign to cross or mut
    for p in selected[:-1]:
        rand_num = random.random()
        for i in range(0, gen_probs):
            if rand_num < gen_probs[i]:
                gen_ops_patches[gen_ops[i][0]].append(copy.deepcopy(p))
                break
    # if there are an odd number of crossover patches, the last patch MUST go into the crossover list
    # otherwise, the patch MUST go into the mut list (so it doesn't create an odd sized crossover batch)
    if 'crossover' in gen_ops_patches and len(gen_ops_patches['crossover']) % 2 == 1:
        gen_ops_patches['crossover'].append(copy.deepcopy(selected[-1]))
    else:
        # just select the first op that isn't crossover
        for d in gen_ops_patches.keys():
            if d != 'crossover':
                gen_ops_patches[d].append(copy.deepcopy(selected[-1]))
    return gen_ops_patches

# NOTE: only subtree mutation is able to change the number of resources used in the population, so first count
# all resources used in all other patches, subtract from max_resource_count, and send that number to subtree_mutate
def create_next_generation(selected, gen_ops, max_num_levels, all_objects, max_resource_count):
    # put even # of vecs in crossover and rest in mutation based on respective probabilities for those operations
    # (fills crossover and mutation vectors from selected vector)
    separated_patches = split_selected_into_gen_ops(selected, gen_ops)
    print 'create next gen'
    # go through each patch group (except for subtree mutation if it exists) and add up the resources in all the patches
    for patch_group in separated_patches.keys():
        if patch_group == 'crossover':
            crossover_patches = crossover(separated_patches['crossover'], max_num_levels, all_objects)
        elif patch_group == 'reproduction':
            reproduction_patches = reproduction(separated_patches['reproduction'])
        elif patch_group == 'point_mutation':
            point_mutation_patches = point_mutate(separated_patches['point_mutate'], all_objects)
    resource_count = 0
    next_generation = []
    for m in point_mutation_patches:
        next_generation.append(copy.deepcopy(m))
        resource_count += m.count
    for c in crossover_patches:
        next_generation.append(copy.deepcopy(c))
        resource_count += c.count
    for r in reproduction_patches:
        next_generation.append(copy.deepcopy(r))
        resource_count += r.count
    resources_left = max_num_levels - resource_count
    # now we can tell the subtree mutation how many resources it may use in generating new subpatches
    if 'subtree_mutation' in separated_patches:
        subtree_mutation_patches = subtree_mutate(separated_patches['subtree_mutate'], max_num_levels, all_objects, resources_left)
    for m in subtree_mutation_patches:
        next_generation.append(copy.deepcopy(m))
        resource_count += m.count
    return next_generation

def subtree_mutate(patches, max_num_levels, objects, max_resource_count):
    print 'mutating patches'
    for i in range(0, len(patches)):
        average_resource_count = max_resource_count / (len(patches) - i)
        numConnections = get_num_connections(patches[i])
        # find cut location that is not the dac connecton (which is the LAST connection when going through cut_subpatch_at_location
        cut_location = random.randint(0,numConnections-2)
        # make cut and alter patch by orphaning appropriate child - return depth of cut (i.e. what level you will start with before adding below the cut) and subpatch
        [dummy_connections, cut_patch, inlet_index, depth, dummy_count_reduction] = cut_subpatch_at_location(patches[i], cut_location) 
        count_of_cut_patch = cut_patch.count
        # create sub patch randomly (look at create patch under max_patch) and attach to child in place
        cut_patch = create_patch(max_num_levels, objects, cut_patch, depth, average_resource_count - count_of_cut_patch, [inlet_index])
        # subtract the resources used by the new patch
        max_resource_count -= cut_patch.count
    # return subtree_mutated patches
    return patches

# find the node at node_location and return its inlet and outlet connection types (both types and number) in lists
def get_node_connection_types(patch, node_location, current_connection_number = 0):
    child_index = 0
    for c in patch.connections:
        # returns inlets and outlets only if they've been found...otherwise, simply updates the connection num so we can track the node_location
        [inlets, outlets, current_connection_num] = get_node_connection_types(patch.children[child_index], node_location, current_connection_number)
        # check to see if we've already found inlets/outlets and now just need to bubble up - note that inlets may be empty if we are changing a terminal
        if outlets != []:
            return inlets, outlets, current_connection_num
        # if we get to the appropriate connection number, return the (sub)patch we want
        if current_connection_num == node_location:
            # the subpatch that we've found's root is the node we want to replace...it's connections refer to inlets and this connection to its outlet connection
            outlets = c.type
            node = patch.children[child_index]
            inlets = []
            for nc in node.connections:
                inlets.extend(nc.type)
            return inlets, outlets, current_connection_num
        # otherwise, increment the current_connection_num as we have just passed over another connection
        else:
            current_connection_num += 1
        child_index += 1
    return [], [], current_connection_num

# return list of objects that could take the appropriate inlet connections and provide appropriate output
# that is not not_object
def get_objects_with_interface(objects, inlets, outlets, not_object = []):
    objects_with_interface = []
    for o in objects:
        # don't include not_object
        if o == not_object:
            continue
        # check to make sure the object has the appropriate number of inlets and outlets
        if len(o.outlets) == len(outlets) and len(o.inlets) == len(inlets):
            # step through outlets and make sure the types are equivalent
            passed_test = True
            for i in range(0, len(outlets)-1):
                if o.outlets[i] != outlets[i]:
                    passed_test = False
            if passed_test:
                # step through inlets and make sure each inlet in inlets can be represented in o.inlets
                for i in range(0, len(inlets) - 1):
                    if inlets[i] not in o.inlets[i].inletTypes:
                        passed_test = False
            # if we've passed all tests it means this object has the same # of ins and outs as passed in interface, the outlet types are consistent with interface, and the inlets can
            # be involved in the connections specified by the interface.
            if passed_test:
                objects_with_interface.exnted(o)
    return objects_with_interface

# swap the node in patch at node_location with the object having
def swap_node(patch, node_location, object):
    print 'needs to be implemented'

def point_mutate(patches, objects):
    # TODO: swap a random node for another with the same type and number of inlets...if one doesn't exist, select another random node
    for i in range(0, len(patches)):
        numConnections = get_num_connections(patches[i])
        # find node location that is not the dac connecton (which is the LAST connection when going through cut_subpatch_at_location
        node_location = random.randint(0,numConnections-2)
        nodes_tried = [node_location]
        # determine signature of patch at node_location
        [object_chosen, inlets, outlets] = get_node_connection_types(patches[i], node_location)
        # determine if other nodes exist with that interface
        objects_with_interface = get_objects_with_interface(objects, inlets, outlets, object_chosen)
        # if there is at least 2 nodes with this interface, there is at least one node to swap with, otherwise, find new node
        while len(objects_with_interface) <= 1 and len(nodes_tried) != patches[i].count:
            node_location = random.randint(0,numConnections-2)
            # keep trying until we get a node we haven't tried yet
            while node_location in nodes_tried:
                node_location = random.randint(0,numConnections-2)
            nodes_tried.extend(node_location)
            # determine signature of patch at node_location
            [object_chosen, inlets, outlets] = get_node_connection_types(patches[i], node_location)
            # determine if other nodes exist with that interface
            objects_with_interface = get_objects_with_interface(objects, inlets, outlets, object_chosen)
        if len(objects_with_interface) > 1:
            objects_to_choose_from = []
            for o in objects_with_interface:
                if o != object_chosen:
                    objects_to_choose_from.append(0)
            object_num = random.randint(0,len(objects_to_choose_from)-2)
            swap_node(patches[i], node_location, objects_to_choose_from[object_num])
        # this means we couldn't find a node to swap
        else:
            print 'couldn\'t find node to swap...just passing through'
    # return point mutated patches
    return patches

# this is currently a simple pass through method, but there are instances where this could be implemented with some structure and therefore a placeholder is here for that reason.
# Either way it models an actual no-op which is conceptually useful for now.
def reproduction(patches):
    return patches

# count the number of connections you pass while traversing the tree and output the result
def get_num_connections(patch):
    connections = 0
    child_index = 0
    # go through all patch connections
    for c in patch.connections:
        # add the number of connections of the subpatch below this child
        connections += get_num_connections(patch.children[child_index])
        connections += 1
        child_index += 1
    return connections

# find subpatch at cut_location and remove it...also return the subpatch whose root has the cut as one of its children
def cut_subpatch_at_location(patch, cut_location, depth = 1, connections = 0):
    # cut_patch starts off empty, so that if we fill it, we start returning up the recursive chain
    cut_patch = []
    # index of the child c refers to
    child_index = 0
    # go through all patch connections
    for c in patch.connections:
        # return the number of connections below this connection, the cut_patch if one has been cut, and the depth of the cut
        # NOTE: we start with a depth of 1 and increment with each recursive call
        [connections, cut_patch, inlet_index, depth, count_reduction] = cut_subpatch_at_location(patch.children[child_index], cut_location, depth + 1, connections)
        # if the cut_patch returned is not empty, we've already found our cut. So keep returning up the recursive chain until we pop out
        if cut_patch != []:
            # update this subpatches count based on how many objects we cut below it
            patch.count -= count_reduction
            return connections, cut_patch, inlet_index, depth, count_reduction
        # if we made it to our cut_location, cut off our children from this index, set cut_patch to this new patch, and return appropriate info
        if (connections == cut_location):
            num_connections_deleting = get_num_connections(patch.children[child_index])
            patch.count -= (num_connections_deleting+1)
            patch.children[child_index] = []
            patch.connections[child_index] = []
            cut_patch = patch
            # TODO: must decrease patch.count appropriately
            return connections, cut_patch, child_index, depth, num_connections_deleting+1
        # add 'this' connection
        connections += 1
        # update child index for next iteration
        child_index += 1
    # if we don't find cut_location, keep moving along, but decrease depth by 1 since we are popping out a recursive cal
    return connections, cut_patch, 0, depth - 1, 0

def crossover(patches, max_num_levels, objects):
    print 'crossover patches'
    # transfer patches from crossover_patches into already_used and when complete, transfer all of these back to crossover_patches
    already_used = []
    in_limbo = []
    output_patches = []
    # will create N/2 pairs if num of patches is N
    for i in range(0, len(patches)/2):
        # select a random patch from the list that hasn't already been used
        random_num = random.randint(0,len(patches)-1)
        # pop off first patch to be used
        first_patch = patches.pop(random_num)
        # select a random patch from the list 
        random_num = random.randint(0,len(patches)-1)
        second_patch = patches.pop(random_num)
        pass_through = False
        '''
        test whether patches can be crossed...if not, grab another. If none can be crossed with first_patch, just pass patches through to children
        note that we are passing in the first child of each...this is because we don't want to cross at the dac level
        '''
        # cross connections will contain pairs of connections that CAN be crossed 
        cross_connections = can_cross_on_connections(first_patch,second_patch)
        while cross_connections == []:
            # if length of patches is 0, we've tried all patches and none can cross with first_patch, so just pass through
            if len(patches) == 0:
                pass_through = True
                # use first selected second patch to pass through
                second_patch = in_limbo.pop(0)
                # place all other patches in limbo back in patches
                patches.extend(in_limbo)
                break
            # remove second_patch from the running!
            in_limbo.append(second_patch)
            random_num = random.randint(0,len(patches)-1)
            second_patch = patches.pop(random_num)
            cross_connections = can_cross_on_connections(first_patch.children[0],second_patch.children[0])
        if pass_through:
            already_used.append(first_patch)
            already_used.append(second_patch)
            output_patches.append(first_patch)
            output_patches.append(second_patch)
        else:
            already_used.append(first_patch)
            already_used.append(second_patch)
            [child1, child2] = cross(first_patch,second_patch,cross_connections)
            output_patches.append(child1)
            output_patches.append(child2)
    return output_patches

# find connections that two patches can cross on and place all combinations in [input_connection,output_connection] lists
def can_cross_on_connections(first_patch, second_patch):
    crossConnections = []
    # get all input and output connection types for first and second patch
    print 'determining if patches can cross'
    # find all connection types in first_patch (NOT including dac~, which is the only connection of the root node)
    first_patch_out_connections = get_all_output_connection_types(first_patch.children[0], True)
    # find all connection types in second_patch (NOT including dac~, which is the only connection of the root node)
    second_patch_in_connections = get_all_input_connection_types(second_patch.children[0], True)
    # find all connection types in second_patch (NOT including dac~, which is the only connection of the root node)
    first_patch_in_connections = get_all_input_connection_types(first_patch.children[0], True)
    # find all connection types in second_patch (NOT including dac~, which is the only connection of the root node)
    second_patch_out_connections = get_all_output_connection_types(second_patch.children[0], True)
    # go through each first_patch input connection
    fConnectionNumber = 0
    for f_input in first_patch_in_connections:
        second_patch_candidates = []
        sConnectionNumber = 0
        # find all output connections from second_patch who have at least one outlet type that would match with at least one inlet type of this inlet    
        for s_output in second_patch_out_connections:
            intersection = [val for val in f_input if val in s_output]
            # this f output can connect to an f input
            if intersection != []:
                second_patch_candidates.append(sConnectionNumber)
            sConnectionNumber += 1
        # go through each second_patch outlet in this list
        for sConnectionNum in second_patch_candidates:
            # find corresponding inlet types involved in the second patch connection
            inletTypes = second_patch_in_connections[sConnectionNum]
            # if corresponding outlet types involved in first patch connection intersect with these inlet types, then cross is possible
            outletTypes = first_patch_out_connections[fConnectionNumber]
            intersection = [val for val in inletTypes if val in outletTypes]
            if intersection != []:
                crossConnections.append([fConnectionNumber,sConnectionNum])
        fConnectionNumber += 1
    return crossConnections    
    
#!!!!!!!!!!!!!!!!!! - Must make sure to return all 'possible' connections something would output or take as input. This is because we are
# only looking for possible connectability between objects and NOT looking at just connections. So, we can't look at connections, but instead need to 
# retrieve the output or input object in the connection and look at their inlet and outlet involved in the connection and find the types at that level
# before a type is chosen.
    
# walk through depth-first to get all possible connection types. If one_to_one is set to True, a 1-1 correspondence is maintained between
# connections and the number of items in the returned list, so that multiple possible connection types for one connection are stuffed into 
# a list within the connection list
def get_all_input_connection_types(patch, one_to_one=False):
    connections = []
    child_index = 0
    # go through all patch connections
    for c in patch.connections:
        if one_to_one:
            # first extend with all this child's connection types
            connections.extend(get_all_input_connection_types(patch.children[child_index],one_to_one=True))
            # get the inlet object associated with this connection
            cInlet = patch.root.inlets[c.inlet]
            # if this inlet has more than one type, append the list of types to our connections list
            if len(cInlet.inletTypes) > 1:
                connections.append(cInlet.inletTypes)
            # if this inlet has one type, just extend our list
            else:
                connections.extend([cInlet.inletTypes])
        else:
            # first extend with all this child's connection types
            connections.extend(get_all_input_connection_types(patch.children[child_index]))
            # get the inlet associated with this connection
            #cInlet = patch.children[child_index].inlets[c.inlet]
            cInlet = patch.root.inlets[c.inlet]
            # extend with connection to child
            connections.extend(cInlet.inletTypes)
        # increment which child we should get all connections for next
        child_index += 1
    return connections
        
def get_all_output_connection_types(patch, one_to_one=False):
    connections = []
    child_index = 0
    for c in patch.connections:
        if one_to_one:
            # first extend with all this child's connection types
            connections.extend(get_all_output_connection_types(patch.children[child_index],one_to_one=True))
            # connections.append(patch.children[child_index].outlets[c.outlet])
            connections.append(patch.children[child_index].root.outlets)
        else:
            # first extend with all this child's connection types
            connections.extend(get_all_output_connection_types(patch.children[child_index]))
            # extend with connection to child
            #connections.extend(patch.children[child_index].outlets[c.outlet])
            connections.extend(patch.children[child_index].root.outlets)
        child_index += 1
    return connections
        
# cross_connections holds combos of connections that can be swapped
def cross(first_patch, second_patch, cross_connections):
    random_num = random.randint(0,len(cross_connections)-1)
    cross_connection = cross_connections[random_num]
    first_patch_connection_number = cross_connection[0]
    second_patch_connection_number = cross_connection[1]
    # cross at that connection, making sure all data is transferred appropriately
    [sub_patch_1, dummy] = get_subpatch_at_connection(first_patch.children[0], first_patch_connection_number)
    # clear parent pointer to be complete
    sub_patch_1 = copy.deepcopy(sub_patch_1)
    sub_patch_1.parent = []
    [sub_patch_2, dummy] = get_subpatch_at_connection(second_patch.children[0], second_patch_connection_number)
    # clear parent pointer to be complete
    sub_patch_2 = copy.deepcopy(sub_patch_2)
    sub_patch_2.parent = []
    [dummy1, dummy2] = replace_subpatch_at_connection(first_patch,sub_patch_2,first_patch_connection_number)
    [dummy1, dummy2] = replace_subpatch_at_connection(second_patch,sub_patch_1,second_patch_connection_number)
    return first_patch,second_patch

# must walk through in the same order the connection list was generated (depth-first) ... current_connection_num allows us to keep track of which connection we are on
# return ([],current_connection_num) if desired_connection_number is not equal to current_connection_num and (subpatch,current_connection_num) below connection if equal
def get_subpatch_at_connection(patch, desired_connection_num, current_connection_num = 0):
    child_index = 0
    for c in patch.connections:
        # first extend with all this child's connection types
        [subpatch, current_connection_num] = get_subpatch_at_connection(patch.children[child_index],desired_connection_num,current_connection_num)
        # check to see if we've already found connection and now just need to bubble up
        if subpatch != []:
            return subpatch, current_connection_num
        # if we get to the appropriate connection number, return the (sub)patch we want
        if current_connection_num == desired_connection_num:
            return patch.children[child_index], current_connection_num
        # otherwise, increment the current_connection_num as we have just passed over another connection
        else:
            current_connection_num += 1
        child_index += 1
    return [], current_connection_num
        
# must walk through in the same order the connection list was generated (depth-first)
# walk through to appropriate connection number (just like with get_subpatch_at_connection), but instead of returning the appropriate subpatch, 
# replace it with subpatch passed in
def replace_subpatch_at_connection(patch,subpatch,desired_connection_num, current_connection_num=0):
    child_index = 0
    for c in patch.connections:
        # first extend with all this child's connection types
        done, current_connection_num = replace_subpatch_at_connection(patch.children[child_index],subpatch,desired_connection_num,current_connection_num)
        # check to see if we've already found connection and now just need to bubble up
        if done:
            return done, current_connection_num
        # if we get to the appropriate connection number, return the (sub)patch we want
        if current_connection_num == desired_connection_num:
            patch.children[child_index] = subpatch
            subpatch.parent = patch
            return True, current_connection_num
        # otherwise, increment the current_connection_num as we have just passed over another connection
        else:
            current_connection_num += 1
        child_index += 1
    return False, current_connection_num
    
'''
#---------------------------------------------------------------------
// check for whether # connections equals # objects at each level
bool testForProblems(vector<MaxPatch> patches)
{
    for (int i = 0; i < patches.size(); i++)
    {
        // there is an issue somewhere
        if (!doObjectsMatchConnections(patches[i])) 
        {
            return true;
        }
    }
    // no problems
    return false;
}

bool doObjectsMatchConnections(MaxPatch patch)
{
    if (patch.objects.size() == 0) 
    {
        return true;
    }
    else 
    {
        if (patch.objects.size() != patch.connections.size())
        {
            return false;
        }
        else
        {
            for (int i = 0; i < patch.objects.size(); i++) 
            {
                if (!doObjectsMatchConnections(*patch.objects[i]))
                {
                    return false;
                }
            }
            return true;
        }
    }
}
'''
