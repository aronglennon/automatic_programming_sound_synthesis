'''
TODO: MORE LOGGING!!!
TOOD: MAX LOGGING??? CAN WE PRE-EMPTIVELY KNOW AUDIO ISN'T FLOWING IN MAX AND TRY AGAIN? JS?
'''
#from maxclasses import predicates
from maxclasses.max_patch import create_patch_from_scratch
from maxclasses.max_object import get_max_objects_from_file
from geneticoperators.ga_ops import create_next_generation, select_patches, update_all_parameters
from features.features_functions import get_features
from similarity.similarity_calc import get_similarity
from resource_limitations.resource_limitations import get_max_tree_depth, get_max_resource_count
from mysqldb.db_commands import mysql_object
import math
from optparse import OptionParser
import sys, random, copy
from datetime import datetime
import numpy as np
import threading

# TODO: turn into config params
DEBUG = False
OBJ_LIST_FILE = '/etc/max/object_list.txt'
TARGET_FILE = '/var/data/max/results_target.wav'
JS_FILE_ROOT =  '/etc/max/js_file'
TEST_ROOT = '/var/data/max/output'
NUM_GENERATIONS = 200
PATCH_TYPE = 'synthesis'

POPULATION_SIZE = 10    # population size
CONCURRENT_PATCHES = 5
INIT_MAX_TREE_DEPTH = 5 # init limit on any one individuals depth
FINAL_MAX_TREE_DEPTH = 10
INIT_RESOURCE_COUNT = 1000
FINAL_RESOURCE_COUNT = 5000
SUBGROUPS = 1
EXCHANGE_FREQUENCY = 10
EXCHANGE_PROPORTION = 0.10
SIMULATED_ANNEALING_SIZE = 10

class calculateFitnessThread (threading.Thread):
    def __init__ (self, threadID, patch, js_filename, test_filename, feature_type, target_features, similarity_measure, population, max_tree_depth, all_objects, warp_factor = 1.0, simulated_annealing = False):
        threading.Thread.__init__ (self)
        self.threadID = threadID
        self.patch = patch
        self.js_filename = js_filename
        self.test_filename = test_filename
        self.feature_type = feature_type
        self.target_features = target_features
        self.similarity_measure = similarity_measure
        self.population = population
        self.all_objects = all_objects
        self.max_tree_depth = max_tree_depth
        self.warp_factor = warp_factor  # warp factor is necessary for IFFs
        self.simulated_annealing = simulated_annealing
        
    def run(self):
        self.patch.start_max_processing(self.js_filename, self.test_filename, self.feature_type, PATCH_TYPE) 
        self.patch.fitness = get_similarity(self.target_features,self.patch.data, self.similarity_measure, self.warp_factor)
        # if nan, create new random patch, calculate fitness, if not nan, use to  replace
        while (np.isnan(self.patch.fitness)):
            auto_gen_patch = create_patch_from_scratch(self.max_tree_depth, self.all_objects, resources_to_use = self.patch.count)
            auto_gen_patch.start_max_processing(self.js_filename, self.test_filename, self.feature_type)
            auto_gen_patch.fitness = get_similarity(self.target_features,auto_gen_patch.data, self.similarity_measure, self.warp_factor)
            loc = self.population.index(self.patch)
            self.population[loc] = auto_gen_patch
            self.patch = auto_gen_patch
        # if there is no simulated annealing, exit
        if not self.simulated_annealing:
            return
        fitness_threshold = 0
        for i in range (0, SIMULATED_ANNEALING_SIZE):
            new_fitness = False
            temperature_value = i + 1
            # METROPOLIS-HASTINGS SAMPLING FOR NEIGHBORS ------------------------
            # select a neighbor
            while not new_fitness:
                # generate random number to test ratio of this patch's fitness to the last CHOSEN patch's fitness to
                u = random.uniform(0.0, 1.0)
                auto_gen_patch = update_all_parameters(self.patch)
                auto_gen_patch.start_max_processing(self.js_filename, self.test_filename, self.feature_type, PATCH_TYPE)
                auto_gen_patch.fitness = get_similarity(self.target_features,self.patch.data, self.similarity_measure, self.warp_factor)
                # if nan, create new random patch, calculate fitness, if not nan, use to  replace
                while (np.isnan(auto_gen_patch.fitness)):
                    auto_gen_patch = update_all_parameters(self.patch)
                    auto_gen_patch.start_max_processing(self.js_filename, self.test_filename, self.feature_type)
                    auto_gen_patch.fitness = get_similarity(self.target_features,auto_gen_patch.data, self.similarity_measure, self.warp_factor)
                    loc = self.population.index(self.patch)
                # ratio of this patch's fitness to the last CHOSEN patch's fitness
                alpha = np.minimum(1.0, auto_gen_patch.fitness/fitness_threshold)
                # if a uniformly random number between 0.0 and 1.0 is less than the ratio above, keep this patch and set it's fitness as the new
                # denominator in the ratio calculated
                if u <= alpha:
                    new_fitness = True
                    fitness_threshold = auto_gen_patch.fitness
            # if we've made it here, we've successfully found a neighbor meeting the M-H criteria
            # now, determine if we move in this direction or not
            if auto_gen_patch.fitness >= self.patch.fitness:
                self.population[loc] = auto_gen_patch
                self.patch = auto_gen_patch
            else:
                # determine the acceptance probability based on the temperature and the two fitness values
                probability = math.exp(-(auto_gen_patch.fitness - self.patch.fitness)/temperature_value)
                random_num = random.random()
                if random_num < probability:
                    self.population[loc] = auto_gen_patch
                    self.patch = auto_gen_patch

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
    if init_method is None:
        init_method = 'grow'
    resource_limitation_type = parameters[0][3]
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
    tree_depth_type = parameters[0][12]
    if tree_depth_type is None:
        tree_depth_type = 'static'
    feature_type = parameters[0][13]
    if feature_type is None:
        feature_type = 'nlse'
    similarity_measure = parameters[0][14]
    if similarity_measure is None:
        similarity_measure = 'SIC-DPLA'
    selection_type = parameters[0][15]
    if selection_type is None:
        selection_type = 'fitness-proportionate'
    atypical_flavor = parameters[0][16]
    if atypical_flavor == 'PADGP':
        # update num of subgroups and population size if PADGP
        SUBGROUPS = 5
        POPULATION_SIZE /= SUBGROUPS
    
    # log run start time    
    run_start = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    testrun_id = mysql_obj.new_test_run(run_start)
    if testrun_id == []:
        sys.exit(0)
    
    # file containing all objects to be used
    object_list_file = open(OBJ_LIST_FILE, 'r')
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
    populations = []
    max_tree_depth = INIT_MAX_TREE_DEPTH
    resource_count = INIT_RESOURCE_COUNT / SUBGROUPS
    for i in range(0, SUBGROUPS):
        population = []
        for j in range (0, POPULATION_SIZE):
            average_resource_count = resource_count / (POPULATION_SIZE - j)
            if init_method == 'ramped_half_and_half':
                if i % 2 == 0:
                    this_init = 'grow'
                else:
                    this_init = 'full'
                # the following keeps the average init tree depth the same, which likely maintains a similar initial resource allotment
                this_max_tree_depth = int(max_tree_depth/2 + j*max_tree_depth/POPULATION_SIZE)
                auto_gen_patch = create_patch_from_scratch(this_max_tree_depth, all_objects, init_type = this_init, resources_to_use = average_resource_count)
            else:
                auto_gen_patch = create_patch_from_scratch(max_tree_depth, all_objects, init_type = init_method, resources_to_use = average_resource_count)
            #print auto_gen_patch.patch_to_string()
            resource_count -= auto_gen_patch.count
            population.append(auto_gen_patch)
        populations.append(population)
    # get features for target file - NOTE: should be 2D numpy array
    target_features = get_features(TARGET_FILE, feature_type)
    # --- MAIN LOOP ---
    warp_factor = 0.0
    for i in range(0, NUM_GENERATIONS):
        if atypical_flavor == "PADGP":
            # check if the generation requires exchange
            if NUM_GENERATIONS % EXCHANGE_FREQUENCY == 0 and NUM_GENERATIONS != 0:
                # determine who is sending patches to who
                received = []
                for i in range(0, SUBGROUPS):
                    send_to = random.randint(0, SUBGROUPS-1)
                    while send_to in received or send_to == i:
                        send_to = random.randint(0, SUBGROUPS-1)
                    received.append(send_to)
                # gather groups of the swap_patches
                swap_amount = int(POPULATION_SIZE * EXCHANGE_PROPORTION)
                temp_main_populations = []
                temp_swap_populations = []
                for population in populations:
                    temp_main_population = []
                    temp_swap_population = []
                    index_list = random.sample(xrange(len(population)), swap_amount)
                    for i in range(0, len(population)):
                        if i in index_list:
                            temp_swap_population.append(copy.deepcopy(population[i]))
                        else:
                            temp_main_population.append(copy.deepcopy(population[i]))
                    temp_main_populations.append(temp_main_population)
                    temp_swap_populations.append(temp_swap_population)
                # exchange by extending patch lists
                for i in range(0, len(received)):
                    populations[i] = temp_main_populations[i]
                    populations[i].extend(temp_swap_populations[received[i]])
        elif atypical_flavor == 'IFF':
            # we start at the most significant warp and slowly wear it off over time
            warp_factor = float(NUM_GENERATIONS-i)/NUM_GENERATIONS
        elif atypical_flavor == 'simulated annealing':
            simulated_annealing = True
        else:
            simulated_annealing = False
            warp_factor = 0.0
        for j in range(0, SUBGROUPS):
            max_tree_depth = get_max_tree_depth(INIT_MAX_TREE_DEPTH, FINAL_MAX_TREE_DEPTH, NUM_GENERATIONS, tree_depth_type, i)
            resource_count = get_max_resource_count(INIT_RESOURCE_COUNT, FINAL_RESOURCE_COUNT, NUM_GENERATIONS, resource_limitation_type, i)
            for k in range(0, len(population)/CONCURRENT_PATCHES):
                fitnessThreads = []
                for l in range(0, CONCURRENT_PATCHES):
                    this_patch = populations[j][k*CONCURRENT_PATCHES + l]
                    fitnessThreads.append(calculateFitnessThread(l, this_patch, JS_FILE_ROOT + ('%d' % l) + '.js', TEST_ROOT + ('%d' % l) + '.wav', feature_type, target_features, similarity_measure, populations[j], max_tree_depth, all_objects, warp_factor, simulated_annealing))
                    fitnessThreads[l].start()
                [l.join() for l in fitnessThreads]
            # sort by fitness
            populations[j].sort(key = lambda x:x.fitness, reverse = True)
            max_gen_fitness = populations[j][0].fitness
            min_gen_fitness = populations[j][-1].fitness
            print 'Max gen fitness %f' % max_gen_fitness
            print 'Min gen fitness %f' % min_gen_fitness
            # TODO: store STATE of system in case of crash
            store_state(mysql_obj, testrun_id, i, populations[j], j, int(options.parameter_set), max_tree_depth, resource_count)
            # first generation
            if i == 0 and j == 0:
                best_patch = populations[0][0]
            # check if this fitness is greater than the last best fitness
            else:
                if populations[j][0].fitness > best_patch.fitness:                    
                    best_patch = populations[j][0]
            selected = select_patches(populations[j], selection_type)                        # fitness proportionate selection
            # create next generation of patches and place them in allPatches
            populations[j] = create_next_generation(selected, gen_ops, max_tree_depth, all_objects, resource_count)
    # save off best of run
    run_end = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    mysql_obj.close_test_run(testrun_id, run_end)

def store_state(mysql_obj, testrun_id, generation_number, population_data, subgroup, parameter_set, max_tree_depth, resource_count):
    for p in population_data:
        if (mysql_obj.insert_full_test_data(testrun_id, generation_number, p.patch_to_string(), p.fitness, subgroup, parameter_set, max_tree_depth, resource_count, PATCH_TYPE, EXCHANGE_FREQUENCY, EXCHANGE_PROPORTION, SIMULATED_ANNEALING_SIZE) == []):
            print 'test data not inserted for unknown reason'

if __name__ == "__main__":
    main() 