'''
Generate 1000 random patches using Metropolis-Hastings
Perform each gen op on these patches in 10 different ways (i.e. to get 10 different neighbors)
and use the one with greatest fitness (i.e. Tournament Selection).
Calculate NSC from entire cloud.
'''
#from maxclasses import predicates
from maxclasses.max_patch import create_patch_from_scratch
from maxclasses.max_object import get_max_objects_from_file
from geneticoperators.fitness import change_fitness_to_probability
from geneticoperators.ga_ops import create_next_generation, select_patches_by_fitness
from features.features_functions import get_features
from similarity.similarity_calc import get_similarity
from resource_limitations.resource_limitations import get_max_tree_depth
from mysqldb.db_commands import mysql_object
import wave, random
from optparse import OptionParser
import sys
from datetime import datetime
import numpy as np

# TODO: turn into config params
# TOOD: rework all code - currently, just a copy over from max_main
DEBUG = False
OBJ_LIST_FILE = '/etc/max/object_list.txt'
SAMP_MFCC_FILE = '/var/data/max/output.wav'
TARG_MFCC_FILE = '/var/data/max/results_target.wav'

POPULATION_SIZE = 1000    # population size
TOURNAMENT_SIZE = 10
INIT_MAX_TREE_DEPTH = 5 # init limit on any one individuals depth

def main():
    # get all options
    parser = OptionParser()
    parser.add_option("--parameter_set", action="store", dest="parameter_set", help="The id of the parameter set to use")
    
    (options, []) = parser.parse_args()
    
    # create DB object to track/log results
    mysql_obj = mysql_object(sameThread = True)
    parameters = mysql_obj.lookup_parameter_set(int(options.parameter_set))
    # make sure the paramter set is for a full test
    if parameters[0][1] != 'gen_ops':
        sys.exit(0)
    # grab all other parameters
    init_method = parameters[0][2]
    gen_ops = []
    if parameters[0][4] is None:
        sys.exit(0)
    else:
        gen_ops.append([parameters[0][4]])
    if parameters[0][6] is None:
        gen_ops[0].append(1.00) # if there is no other gen op, disregard prob, since it must be 1.00
    else:
        gen_ops[0].append(parameters[0][5])
        gen_ops.append([parameters[0][6]])
        if parameters[0][8] is None:
            gen_ops[1].append(1.00 - gen_ops[0][1])
        else:
            gen_ops[1].append(parameters[0][7])
            gen_ops.append([parameters[0][8]])
            if parameters[0][10] is None:
                gen_ops[2].append(1.00 - gen_ops[0][1] - gen_ops[1][1])
            else:
                gen_ops[2].append(parameters[0][9])
                gen_ops.append([parameters[0][10], 1.00 - gen_ops[0][1] - gen_ops[1][1] - gen_ops[2][1]])
    feature_type = parameters[0][13]
    similarity_measure = parameters[0][14]
    
    # log run start time    
    run_start = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    testrun_id = mysql_obj.new_test_run(run_start)
    if testrun_id == []:
        sys.exit(0)
    
    # file containing all objects to be used
    object_list_file = open(OBJ_LIST_FILE, 'r')
    # file containing mfccs of audio output from target
    target_features_file = wave.open(TARG_MFCC_FILE, 'r')
    
    # fill all object lists from file
    all_objects = get_max_objects_from_file(object_list_file)
    object_list_file.close()
    
    # get features for target file - NOTE: should be 2D numpy array
    target_features = get_features(target_features_file, feature_type)
    target_features_file.close()
    
    # create population of max objects
    max_tree_depth = INIT_MAX_TREE_DEPTH
    this_max_tree_depth = max_tree_depth
    fitness_threshold = 0
    for i in range (0, POPULATION_SIZE-1):
        new_fitness = False
        # METROPOLIS-HASTINGS SAMPLING ------------------------
        while not new_fitness:
            # generate random number to test ratio of this patch's fitness to the last CHOSEN patch's fitness to
            u = random.uniform(0.0, 1.0)
            if init_method == 'ramped_half_and_half':
                if i % 2 == 0:
                    this_init = 'grow'
                else:
                    this_init = 'full'
                # the following keeps the average init tree depth the same, which likely maintains a similar initial resource allotment
                this_max_tree_depth = int(max_tree_depth/2 + i*max_tree_depth/POPULATION_SIZE)
                auto_gen_patch = create_patch_from_scratch(this_max_tree_depth, all_objects, this_init)
            else:
                this_init = init_method
                auto_gen_patch = create_patch_from_scratch(this_max_tree_depth, all_objects, this_init)
            auto_gen_patch.start_max_processing(SAMP_MFCC_FILE, feature_type)
            auto_gen_patch.fitness = get_similarity(target_features,auto_gen_patch.data, similarity_measure)
            # if nan, create new random patch, calculate fitness, if not nan, use to  replace
            while (np.isnan(auto_gen_patch.fitness)):
                auto_gen_patch = create_patch_from_scratch(this_max_tree_depth, all_objects, this_init)
                auto_gen_patch.start_max_processing(SAMP_MFCC_FILE, feature_type)
                auto_gen_patch.fitness = get_similarity(target_features,auto_gen_patch.data, similarity_measure)
            # ratio of this patch's fitness to the last CHOSEN patch's fitness
            alpha = np.minimum(1.0, auto_gen_patch.fitness/fitness_threshold)
            # if a uniformly random number between 0.0 and 1.0 is less than the ratio above, keep this patch and set it's fitness as the new
            # denominator in the ratio calculated
            if u <= alpha:
                new_fitness = True
                fitness_threshold = auto_gen_patch.fitness
        # ------------------------------------------------------
        
        # generate 10 neighbors using genops        
        copies = []
        for i in range (0, TOURNAMENT_SIZE-1):
            copies.append(auto_gen_patch)
        neighbors = create_next_generation(copies, gen_ops, max_tree_depth, all_objects)
        # sort neighbors by fitness
        for n in neighbors:
            n.fitness = get_similarity(target_features,n.data, similarity_measure)
            # if similarity fails, generate a new patch
            while (np.isnan(n.fitness)):
                n = create_next_generation(auto_gen_patch, gen_ops, max_tree_depth, all_objects)
                n.fitness = get_similarity(target_features,n.data, similarity_measure)
        neighbors.sort(key = lambda x:x.fitness, reverse = True)
        best_neighbor = neighbors[0]
        # store patch, fitness, best neighbor, its fitness
        mysql_obj.insert_genops_test_data(testrun_id, i, TARG_MFCC_FILE, auto_gen_patch.patch_to_string(), auto_gen_patch.fitness, best_neighbor.patch_to_string(), best_neighbor.fitness)
    run_end = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    mysql_obj.close_test_run(testrun_id, run_end)

if __name__ == "__main__":
    main() 