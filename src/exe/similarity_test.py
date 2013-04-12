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

'''
NOTES:
- Must compare aligned-Euclidean, global DTW, DPLA (just use version of SIC-DPLA - talk about this in dissertation), SIC-DPLA
- N experiments each of:
-- Slight global time scaling (rand between 2-5%) combined with time shifting (rand between 100-500ms)
-------------- params: easy, test_run, file, time_scale_and_stretch, scale_percent, shift_amount (ms)
-- Local time warping (rand selected such that warping path does not diverge from diagonal by more than 5 frames)
-------------- params: easy, test_run, file, time_warping, threshold on max warp divergence, record entire path(?)
-- Random sample deletion (random select segments of various sizes no more than 2-5% of total content)
-------------- params: easy, test_run, file, segment_deletion, deleted content, num_segments, max_segment, min_segment, average_segment
-- Range extension of stable timbral content randomly selected and totalling between 2-5% of all content (will have to find places where timbre is stable in test files)
-------------- params: easy, test_run, file, stable_content_extension, total_extension, num_extension, max_extension, min_extension, average_extension

-- introduce new timbral content (from other files?) between 10-50% of file length, while randomly deleting other content
-------------- params: severe, test_run, file, introduce_content, total_percent_indtroduction, total_percent_deletion, introduction_from_where, num_introduction, num_deletion, max/min/avg introduction and deletion
-- re-order rand sequences within content (choosing subseqs between 10-20% of file length and swapping out of order up to 5 times)
-------------- params: severe, test_run, file, re-order, number swaps, max_size, min_size, total_size, average_size
-- random insertion of repetitions paired with random deleting of non-repetitive segments (by choosing subseqs between 10-20% file length and repeating up to 3 times)
-------------- params: severe, test_run, file, insert_repetition, number unique repetitions, max_reps for unique, min_reps for unique, total reps, average reps, total_length reps, total_length deletes, num segment deletes, max delete, min delete, max rep length, min rep length, avg_rep_length, avg_delete_length
-- applying severe temporal warpings (rand selected such taht warping path diverges at least more than 10 frames once during length of file)
-------------- params: severe, test_run, file, time warping, threshold on min warp divergence, record entire path(?)

Given different params to keep track of, each test will have a different table to record those into...we'll just go through random test runs and insert rows.
'''

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