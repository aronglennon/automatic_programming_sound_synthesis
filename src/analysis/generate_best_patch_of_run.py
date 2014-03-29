#from maxclasses import predicates
from maxclasses.max_patch import create_patch_from_scratch, string_to_patch
from maxclasses.max_object import get_max_objects_from_file
from geneticoperators.ga_ops import create_next_generation, select_patches, update_all_parameters
from features.features_functions import get_features
from similarity.similarity_calc import get_similarity
from mysqldb.db_commands import mysql_object
import math
from optparse import OptionParser
import sys, random, copy
from datetime import datetime
import numpy as np
import threading
from maxclasses.javascript import fill_JS_file

OBJ_LIST_FILE = '/etc/max/general3_object_list.txt'
JS_FILE_NAME =  '/etc/max/js_file_best_patch'

def main():
    sys.setrecursionlimit(10000)
    # get all options
    parser = OptionParser()
    parser.add_option("--test_run", action = "store", dest = "test_run", help = "The id of the parameter set to use")
    
    (options, []) = parser.parse_args()
    
    # create DB object to track/log results
    mysql_obj = mysql_object(sameThread = True)
    # file containing all objects to be used
    object_list_file = open(OBJ_LIST_FILE, 'r')
    # fill all object lists from file
    all_objects = get_max_objects_from_file(object_list_file)
    object_list_file.close()
    
    testrun_id = int(options.test_run)
    results = mysql_obj.get_best_of_run(testrun_id)
    best_patch = string_to_patch(results[0][2], float(results[0][0]), all_objects)
    best_of_run_fitness = float(results[0][0])
    print 'best of run fitness: %0.8f' % best_of_run_fitness 
    best_of_run_generation = float(results[0][1])
    print 'best of run generation: %d' % best_of_run_generation
    fill_JS_file(JS_FILE_NAME, best_patch, 'synthesis')
                
if __name__ == "__main__":
    main() 