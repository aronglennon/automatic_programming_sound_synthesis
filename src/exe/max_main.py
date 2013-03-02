'''
TODO: MORE LOGGING!!!
TOOD: MAX LOGGING??? CAN WE PRE-EMPTIVELY KNOW AUDIO ISN'T FLOWING IN MAX AND TRY AGAIN? JS?
'''
#from maxclasses import predicates
from maxclasses.max_patch import create_patch_from_scratch
from maxclasses.max_object import get_max_objects_from_file
from geneticoperators.fitness import change_fitness_to_probability
from geneticoperators.ga_ops import *
from features.features_functions import get_features
from similarity.similarity_calc import get_similarity
import wave
from optparse import OptionParser
import pickle
from datetime import datetime
import numpy as np

# TODO: turn into config params
DEBUG = False
OBJ_LIST_FILE = '/etc/max/object_list.txt'
SAMP_MFCC_FILE = '/var/data/max/output.wav'
TARG_MFCC_FILE = '/var/data/max/results_target.wav'
NUM_GENERATIONS = 100
CROSSOVER_PROB = 0.8
MUTATION_PROB = 1.0 - CROSSOVER_PROB
NUM_PATCHES = 10
MAX_NUM_LEVELS = 5

def main():
    # get all options
    parser = OptionParser()
    parser.add_option("--similarity", action="store", dest="similarity", help="The similarity method to use")
    parser.add_option("--features", action="store", dest="features", help="The features to use")
    
    (options, args) = parser.parse_args()
    # file containing state information during run
    run_start = datetime.utcnow()
    CURRENT_STATE_FILE = '/var/data/max/state-s-%s-f-%s-r-%s' % (options.similarity, options.features, run_start.strftime("%Y%m%d"))
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
    current_state = {}
    for i in range (0, NUM_PATCHES):
        auto_gen_patch = create_patch_from_scratch(MAX_NUM_LEVELS, all_objects)
        #auto_gen_patch.pretty_print()
        population.append(auto_gen_patch)
    # get features for target file - NOTE: should be 2D numpy array
    target_features = get_features(target_features_file,options.features)
    target_features_file.close()
    # --- MAIN LOOP ---
    for i in range(0, NUM_GENERATIONS):
        for j in range(0, len(population)):
            this_patch = population[j]
            # populate this_patch.data with features from specified file
            this_patch.start_max_processing(SAMP_MFCC_FILE,options.features)
            this_patch.fitness = get_similarity(target_features,this_patch.data, options.similarity)
            # if nan, create new random patch, calculate fitness, if not nan, use to  replace
            while (np.isnan(this_patch.fitness)):
                auto_gen_patch = create_patch_from_scratch(MAX_NUM_LEVELS, all_objects)
                auto_gen_patch.start_max_processing(SAMP_MFCC_FILE,options.features)
                auto_gen_patch.fitness = get_similarity(target_features,auto_gen_patch.data, options.similarity)
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
        current_state['population_%d' % i] = population
        store_state(current_state,CURRENT_STATE_FILE)
        # first generation
        if i == 0:
            best_patch = population[-1]
        # check if this fitness is greater than the last best fitness
        else:
            if (population[-1].fitness + min_gen_fitness) < best_patch.fitness:                    
                best_patch = population[-1]
        # perform fitness proportionate selection
        change_fitness_to_probability(population, "high")                # "low" tells the function that a lower score is considered better and "high" means higher is better
        selected = select_patches_by_fitness(population)                        # fitness proportionate selection
        # put even # of vecs in crossover and rest in mutation based on respective probabilities for those operations
        # (fills crossover and mutation vectors from selected vector)
        [crossover, mutation] = split_selected_into_cross_and_mutation(selected, CROSSOVER_PROB, MUTATION_PROB)           
        # create next generation of patches and place them in allPatches
        population = create_next_generation(crossover, mutation, MAX_NUM_LEVELS, all_objects)
    # save off best of run

def store_state(current_state, state_filename):
    state_file = open(state_filename, 'w')
    pickle.dump(current_state,state_file)
    state_file.close()

if __name__ == "__main__":
    main() 