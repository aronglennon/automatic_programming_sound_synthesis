'''
TODO: MORE LOGGING!!!
TOOD: MAX LOGGING??? CAN WE PRE-EMPTIVELY KNOW AUDIO ISN'T FLOWING IN MAX AND TRY AGAIN? JS?
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
import wave
from optparse import OptionParser
import sys
from datetime import datetime
import numpy as np

# TODO: turn into config params
DEBUG = False
OBJ_LIST_FILE = '/etc/max/object_list.txt'
SAMP_MFCC_FILE = '/var/data/max/output.wav'
TARG_MFCC_FILE = '/var/data/max/results_target.wav'
NUM_GENERATIONS = 100

POPULATION_SIZE = 10    # population size
INIT_MAX_TREE_DEPTH = 5 # init limit on any one individuals depth
INIT_RESOURCE_LIMITATION = 500 # init number of nodes + terminals in population allowed (if RLGP used)

def main():
    # get all options
    parser = OptionParser()
    parser.add_option("--parameter_set", action="store", dest="parameter_set", help="The id of the parameter set to use")
    
    (options, []) = parser.parse_args()
    
    # create DB object to track/log results
    mysql_obj = mysql_object(sameThread = True)
    parameters = mysql_obj.lookup_parameter_set(int(options.parameter_set))
    # make sure the paramter set is for a full test
    if parameters[0][1] != 'full':
        sys.exit(0)
    # grab all other parameters
    init_method = parameters[0][2]
    resource_limitation_type = parameters[0][3]
    gen_ops = []
    if parameters[0][4] is None:
        sys.exit(0)
    else:
        gen_ops.append([parameters[0][4]])
    if parameters[0][6] is None:
        gen_ops[0].append(1.00) # if there is no other gen op, disregard prob, since it must be 1.00
    else:
        gen_ops[0].aapend(parameters[0][5])
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
    tree_depth_type = parameters[0][12]
    feature_type = parameters[0][13]
    similarity_measure = parameters[0][14]
    selection_type = parameters[0][15]
    
    # log run start time    
    run_start = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    testrun_id = mysql_obj.new_test_run(run_start)
    if testrun_id == []:
        sys.exit(0)
    
    # file containing all objects to be used
    object_list_file = open(OBJ_LIST_FILE, 'r')
    # file containing mfccs of audio output from target
    target_features_file = wave.open(TARG_MFCC_FILE, 'r')
    # best patch of run
    best_patch = []
    # min fitness of generation
    min_gen_fitness = 0
    # max fitness of generation
    max_gen_fitness = 0
    # fill all object lists from file
    all_objects = get_max_objects_from_file(object_list_file)
    object_list_file.close()
    
    # create initial population of max objects
    population = []
    max_tree_depth = INIT_MAX_TREE_DEPTH
    for i in range (0, POPULATION_SIZE):
        if init_method == 'ramped_half_and_half':
            if i % 2 == 0:
                this_init = 'grow'
            else:
                this_init = 'full'
            # the following keeps the average init tree depth the same, which likely maintains a similar initial resource allotment
            this_max_tree_depth = int(max_tree_depth/2 + i*max_tree_depth/POPULATION_SIZE)
            auto_gen_patch = create_patch_from_scratch(this_max_tree_depth, all_objects, this_init)
        else:
            auto_gen_patch = create_patch_from_scratch(max_tree_depth, all_objects, init_method)
        #print auto_gen_patch.patch_to_string()
        population.append(auto_gen_patch)
    # get features for target file - NOTE: should be 2D numpy array
    target_features = get_features(target_features_file, feature_type)
    target_features_file.close()
    # --- MAIN LOOP ---
    for i in range(0, NUM_GENERATIONS):
        max_tree_depth = get_max_tree_depth(INIT_MAX_TREE_DEPTH, NUM_GENERATIONS, tree_depth_type)
        for j in range(0, len(population)):
            this_patch = population[j]
            # populate this_patch.data with features from specified file
            this_patch.start_max_processing(SAMP_MFCC_FILE, feature_type) ######################## MAKE WORK WITH MULTIPLE CONCURRENT PATCHES
            this_patch.fitness = get_similarity(target_features,this_patch.data, similarity_measure)
            # if nan, create new random patch, calculate fitness, if not nan, use to  replace
            while (np.isnan(this_patch.fitness)):
                auto_gen_patch = create_patch_from_scratch(max_tree_depth, all_objects)
                auto_gen_patch.start_max_processing(SAMP_MFCC_FILE, feature_type)
                auto_gen_patch.fitness = get_similarity(target_features,auto_gen_patch.data, similarity_measure)
                loc = population.index(this_patch)
                population[loc] = auto_gen_patch
                this_patch = auto_gen_patch
        # sort by fitness
        population.sort(key = lambda x:x.fitness, reverse = True)
        max_gen_fitness = population[0].fitness
        min_gen_fitness = population[-1].fitness
        print 'Max gen fitness %f' % max_gen_fitness
        print 'Min gen fitness %f' % min_gen_fitness
        # TODO: store STATE of system in case of crash
        store_state(mysql_obj, testrun_id, i, population)
        # first generation
        if i == 0:
            best_patch = population[-1]
        # check if this fitness is greater than the last best fitness
        else:
            if (population[-1].fitness + min_gen_fitness) < best_patch.fitness:                    
                best_patch = population[-1]
        # perform fitness proportionate selection
        change_fitness_to_probability(population, "high")                # "low" tells the function that a lower score is considered better and "high" means higher is better
        selected = select_patches_by_fitness(population, selection_type)                        # fitness proportionate selection
        # create next generation of patches and place them in allPatches
        population = create_next_generation(selected, gen_ops, max_tree_depth, all_objects)
    # save off best of run
    run_end = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    mysql_obj.close_test_run(testrun_id, run_end)

def store_state(mysql_obj, testrun_id, generation_number, population_data):
    for p in population_data:
        if (mysql_obj.insert_full_test_data(testrun_id, generation_number, p.patch_to_string(), p.fitness) == []):
            print 'test data not inserted for unknown reason'

if __name__ == "__main__":
    main() 