'''
Generate N different tests of pairs of similar timbral content of various complexity and different content of various complexity.
Test distances given by each similarity measure to determine which is consistently good for both similar and dissimilar test pairs.
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

# TODO: turn into config params, so we store EVERYTHING in DB
# TODO: write distortion functions
DEBUG = False
WAVE_FILE_DIRECTORY = ""
NUM_TESTS = 100

def main():
    # get all options
    parser = OptionParser()
    parser.add_option("--parameter_set", action="store", dest="parameter_set", help="The id of the parameter set to use")
    
    (options, []) = parser.parse_args()
    
    # create DB object to track/log results
    mysql_obj = mysql_object(sameThread = True)
    parameters = mysql_obj.lookup_parameter_set(int(options.parameter_set))
    # make sure the paramter set is for a similarity_measure test
    if parameters[0][1] != 'similarity_measure':
        sys.exit(0)
    # NOTE: do we need the following two? Likely not
    feature_type = parameters[0][13]
    similarity_measure = parameters[0][14]    
    # log run start time    
    run_start = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    testrun_id = mysql_obj.new_test_run(run_start)
    if testrun_id == []:
        sys.exit(0)
    # generate distortion for file in WAVE_FILE_DIRECTORY
    # test using all similarity measures for apples-to-apples comparison
    # store (file_name, distortion_type, distortion_severity, similarity_measure, similarity_score)
    run_end = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    mysql_obj.close_test_run(testrun_id, run_end)

def store_state(mysql_obj, testrun_id, file_name, distortion_type, distortion_severity, similarity_measure, similarity_score):
    if (mysql_obj.insert_similarity_test_data(testrun_id, file_name, distortion_type, distortion_severity, similarity_measure, similarity_score) == []):
        print 'similarity test data not inserted for unknown reason'

if __name__ == "__main__":
    main() 