'''
Generate N different tests of pairs of similar timbral content of various complexity and different content of various complexity.
Test distances given by each similarity measure to determine which is consistently good for both similar and dissimilar test pairs.
'''

#from maxclasses import predicates
from maxclasses.max_patch import create_patch_from_scratch
from maxclasses.max_object import get_max_objects_from_file
from geneticoperators.fitness import change_fitness_to_probability
from geneticoperators.ga_ops import create_next_generation, select_patches_by_fitness
from features.features_functions import *
from distortions.distortions import *
from similarity.similarity_calc import get_similarity
from resource_limitations.resource_limitations import get_max_tree_depth
from mysqldb.db_commands import mysql_object
import wave, struct
from optparse import OptionParser
import sys, random, os, re
from datetime import datetime
import numpy as np

# TODO: turn into config params, so we store EVERYTHING in DB
# TODO: write distortion functions
DEBUG = False
WAVE_FILE_DIRECTORY = "/Users/apg250/git/automatic_programming_sound_synthesis/max_patches/realworld_sounds/for_testing/"
SAVE_DIR = "/Users/apg250/git/automatic_programming_sound_synthesis/similarity_test_files/"   # dir to save all distorted files
NUM_TESTS = 100
MAX_WARP = 5
MIN_WARP = 10

'''
NOTES:
- Must compare aligned-Euclidean, global DTW, DPLA (just use version of SIC-DPLA - talk about this in dissertation), SIC-DPLA
'''

def main():
    random.seed()
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
    # log run start time    
    run_start = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    testrun_id = mysql_obj.new_test_run(run_start)
    if testrun_id == []:
        sys.exit(0)
    for i in range(0, NUM_TESTS):
        # light distortions (one for every file in WAVE_FILE_DIRECTORY
        run_tsts_tests(WAVE_FILE_DIRECTORY, testrun_id, i, mysql_obj)
        run_tw_tests(WAVE_FILE_DIRECTORY, testrun_id, i, None, MAX_WARP, mysql_obj)
        run_sampdel_tests(WAVE_FILE_DIRECTORY, testrun_id, i, mysql_obj)
        run_stableextension_tests(WAVE_FILE_DIRECTORY, testrun_id, i, mysql_obj)
        # heavy distortion
        run_contentintro_tests(WAVE_FILE_DIRECTORY, testrun_id, i, mysql_obj)
        run_reorder_tests(WAVE_FILE_DIRECTORY, testrun_id, i, mysql_obj)
        run_repinsert_tests(WAVE_FILE_DIRECTORY, testrun_id, i, mysql_obj)
        run_tw_tests(WAVE_FILE_DIRECTORY, testrun_id, i, MIN_WARP, None, mysql_obj)
        
    # generate distortion for file in WAVE_FILE_DIRECTORY
    # test using all similarity measures for apples-to-apples comparison
    # store (file_name, distortion_type, distortion_severity, similarity_measure, similarity_score)
    run_end = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    mysql_obj.close_test_run(testrun_id, run_end)

'''
-- Slight global time scaling (rand between 2-5%) combined with time shifting (rand between 100-500ms) (tsts)
-------------- params: easy, test_run, file, time_scale_and_stretch, scale_percent, shift_amount (ms)

NOTE: scaling should be performed on features so as to not change timbral content via pitch shifting
'''
    
    
def run_tsts_tests(directory, test_run, test_case, mysql_obj):
    scale_percent = random.uniform(2.0, 5.0)       # percent of file length
    shift_amount = random.uniform(100.0, 500.0)    # ms
    # for each file in directory, scale, shift - run through all sim measures - insert each result into db
    if os.path.isdir(directory):
        for dirname, dirnames, filenames in os.walk(directory):
            for filename in filenames:   
                wavefile = re.compile('(.*\.wav$)')
                if wavefile.match(filename):
                    test_audio_file = wave.open(dirname+filename, 'r')
                    # get test audio
                    test_audio = get_audio(test_audio_file)
                    # extract features
                    test_features = get_features(dirname+filename, 'nlse')
                    # distort test audio
                    shifted_audio = shift_audio(test_audio, shift_amount/1000.0*test_audio_file.getframerate())
                    # save distorted audio
                    distorted_directory = SAVE_DIR + "/" + str(test_run) + "/" + str(test_case)
                    if not os.path.exists(distorted_directory):
                        os.makedirs(distorted_directory)
                    distorted_file = wave.open(distorted_directory + "/" + filename[:-4] + "shift.wav", 'w')
                    distorted_file.setparams((1, 2, 44100, shifted_audio.shape[0], "NONE", "not compressed"))
                    N = shifted_audio.shape[0]
                    shifted_audio = np.asarray(shifted_audio.flatten()*(2.0 ** (8 * 2 - 1)), dtype = int)
                    shifted_audio = struct.pack('%dh' % N, * shifted_audio)
                    distorted_file.writeframes(shifted_audio)
                    distorted_file.close()
                    # get distorted features
                    shifted_features = get_features(distorted_directory + "/" + filename[:-4] + "shift.wav", 'nlse')
                    scaled_and_shifted_features = scale_features(shifted_features, scale_percent)
                    # calc all similarity values
                    euc_sim = get_similarity(test_features, scaled_and_shifted_features, 'euclidean')
                    dtw_sim = get_similarity(test_features, scaled_and_shifted_features, 'DTW')
                    dpla_sim = get_similarity(test_features, scaled_and_shifted_features, 'DPLA')
                    sic_dpla_sim = get_similarity(test_features, scaled_and_shifted_features, 'SIC-DPLA')
                    # store results in db
                    mysql_obj.insert_tsts_test_data(test_run, test_case, filename, scale_percent, shift_amount, 'euclidean', euc_sim)
                    mysql_obj.insert_tsts_test_data(test_run, test_case, filename, scale_percent, shift_amount, 'DTW', dtw_sim)
                    mysql_obj.insert_tsts_test_data(test_run, test_case, filename, scale_percent, shift_amount, 'DPLA', dpla_sim)
                    mysql_obj.insert_tsts_test_data(test_run, test_case, filename, scale_percent, shift_amount, 'SIC-DPLA', sic_dpla_sim)

    return []

'''
-- Local time warping (rand selected such that warping path does not diverge from diagonal by more than 5 frames for easy and where path diverges at least
once by more than 10 frames for severe)
-------------- params: easy, test_run, file, time_warping, threshold on max warp divergence, record entire path(?)

NOTE: should be performed on features so as to not change timbral content via pitch shifting
'''
def run_tw_tests(directory, test_run, test_case, min_warping_threshold, max_warping_threshold, mysql_obj):
    # for each file in directory, scale, shift - run through all sim measures - insert each result into db
    if os.path.isdir(directory):
        for dirname, dirnames, filenames in os.walk(directory):
            for filename in filenames:   
                wavefile = re.compile('(.*\.wav$)')
                if wavefile.match(filename):
                    # extract features
                    test_features = get_features(dirname+filename, 'nlse')
                    # distort test features
                    [time_warped_features, warping_path] = time_warp_features(test_features, min_warping_threshold, max_warping_threshold)
                    # calc all similarity values
                    euc_sim = get_similarity(test_features, time_warped_features, 'euclidean')
                    dtw_sim = get_similarity(test_features, time_warped_features, 'DTW')
                    dpla_sim = get_similarity(test_features, time_warped_features, 'DPLA')
                    sic_dpla_sim = get_similarity(test_features, time_warped_features, 'SIC-DPLA')
                    # store results in db
                    mysql_obj.insert_tw_test_data(test_run, test_case, filename, min_warping_threshold, max_warping_threshold, warping_path, 'euclidean', euc_sim)
                    mysql_obj.insert_tw_test_data(test_run, test_case, filename, min_warping_threshold, max_warping_threshold, warping_path, 'DTW', dtw_sim)
                    mysql_obj.insert_tw_test_data(test_run, test_case, filename, min_warping_threshold, max_warping_threshold, warping_path, 'DPLA', dpla_sim)
                    mysql_obj.insert_tw_test_data(test_run, test_case, filename, min_warping_threshold, max_warping_threshold, warping_path, 'SIC-DPLA', sic_dpla_sim)
    return []

'''
-- Random sample deletion (random select segments of various sizes no more than 2-5% of total content)
-------------- params: easy, test_run, file, segment_deletion, total amount of deleted content, num_segments, max_segment, min_segment, average_segment
'''
def run_sampdel_tests(directory, test_run, test_case, mysql_obj):
    total_deleted_content = random.uniform(2.0, 5.0)       # percent of file length
    # for each file in directory, scale, shift - run through all sim measures - insert each result into db
    if os.path.isdir(directory):
        for dirname, dirnames, filenames in os.walk(directory):
            for filename in filenames:   
                wavefile = re.compile('(.*\.wav$)')
                if wavefile.match(filename):
                    test_audio_file = wave.open(dirname+filename, 'r')
                    # get test audio
                    test_audio = get_audio(test_audio_file)
                    # extract features
                    test_features = get_features(dirname+filename, 'nlse')
                    # distort test audio
                    [deleted_sample_audio, num_segments, max_segment, min_segment, avg_segment] = delete_samples(test_audio, total_deleted_content)
                    # save distorted audio
                    distorted_directory = SAVE_DIR + "/" + str(test_run) + "/" + str(test_case)
                    if not os.path.exists(distorted_directory):
                        os.makedirs(distorted_directory)
                    distorted_file = wave.open(distorted_directory + "/" + filename[:-4] + "sampdel.wav", 'w')
                    distorted_file.setparams((1, 2, 44100, deleted_sample_audio.shape[0], "NONE", "not compressed"))
                    N = deleted_sample_audio.shape[0]
                    shifted_audio = np.asarray(deleted_sample_audio.flatten()*(2.0 ** (8 * 2 - 1)), dtype = int)
                    shifted_audio = struct.pack('%dh' % N, * shifted_audio)
                    distorted_file.writeframes(shifted_audio)
                    distorted_file.close()
                    # get distorted features
                    deleted_samples_features = get_features(distorted_directory + "/" + filename[:-4] + "sampdel.wav", 'nlse')
                    # calc all similarity values
                    euc_sim = get_similarity(test_features, deleted_samples_features, 'euclidean')
                    dtw_sim = get_similarity(test_features, deleted_samples_features, 'DTW')
                    dpla_sim = get_similarity(test_features, deleted_samples_features, 'DPLA')
                    sic_dpla_sim = get_similarity(test_features, deleted_samples_features, 'SIC-DPLA')
                    # store results in db
                    mysql_obj.insert_sampdel_test_data(test_run, test_case, filename, total_deleted_content, num_segments, max_segment, min_segment, avg_segment, 'euclidean', euc_sim)
                    mysql_obj.insert_sampdel_test_data(test_run, test_case, filename, total_deleted_content, num_segments, max_segment, min_segment, avg_segment, 'DTW', dtw_sim)
                    mysql_obj.insert_sampdel_test_data(test_run, test_case, filename, total_deleted_content, num_segments, max_segment, min_segment, avg_segment, 'DPLA', dpla_sim)
                    mysql_obj.insert_sampdel_test_data(test_run, test_case, filename, total_deleted_content, num_segments, max_segment, min_segment, avg_segment, 'SIC-DPLA', sic_dpla_sim)
    return []

'''
- Range extension of stable timbral content randomly selected and totalling between 2-5% of all content (will have to find places where timbre is stable in test files)
-------------- params: easy, test_run, file, stable_content_extension, total_extension, num_extension, max_extension, min_extension, average_extension
'''
def run_stableextension_tests(directory, test_run, test_case, mysql_obj):
    total_content_extended = random.uniform(2.0, 5.0)       # percent of file length
    # for each file in directory, scale, shift - run through all sim measures - insert each result into db
    if os.path.isdir(directory):
        for dirname, dirnames, filenames in os.walk(directory):
            for filename in filenames:   
                wavefile = re.compile('(.*\.wav$)')
                if wavefile.match(filename):
                    test_audio_file = wave.open(dirname+filename, 'r')
                    # get test audio
                    test_audio = get_audio(test_audio_file)
                    # extract features
                    test_features = get_features(dirname+filename, 'nlse')
                    # distort test audio
                    [stable_extension_audio, num_segments, max_segment, min_segment, avg_segment] = stable_extension(test_audio, total_content_extended)
                    # save distorted audio
                    distorted_directory = SAVE_DIR + "/" + str(test_run) + "/" + str(test_case)
                    if not os.path.exists(distorted_directory):
                        os.makedirs(distorted_directory)
                    distorted_file = wave.open(distorted_directory + "/" + filename[:-4] + "stableextension.wav", 'w')
                    distorted_file.setparams((1, 2, 44100, stable_extension_audio.shape[0], "NONE", "not compressed"))
                    N = stable_extension_audio.shape[0]
                    shifted_audio = np.asarray(stable_extension_audio.flatten()*(2.0 ** (8 * 2 - 1)), dtype = int)
                    shifted_audio = struct.pack('%dh' % N, * shifted_audio)
                    distorted_file.writeframes(shifted_audio)
                    distorted_file.close()
                    # get distorted features
                    stable_extension_features = get_features(distorted_directory + "/" + filename[:-4] + "stableextension.wav", 'nlse')
                    # calc all similarity values
                    euc_sim = get_similarity(test_features, stable_extension_features, 'euclidean')
                    dtw_sim = get_similarity(test_features, stable_extension_features, 'DTW')
                    dpla_sim = get_similarity(test_features, stable_extension_features, 'DPLA')
                    sic_dpla_sim = get_similarity(test_features, stable_extension_features, 'SIC-DPLA')
                    # store results in db
                    mysql_obj.insert_stableextension_test_data(test_run, test_case, filename, total_content_extended, num_segments, max_segment, min_segment, avg_segment, 'euclidean', euc_sim)
                    mysql_obj.insert_stableextension_test_data(test_run, test_case, filename, total_content_extended, num_segments, max_segment, min_segment, avg_segment, 'DTW', dtw_sim)
                    mysql_obj.insert_stableextension_test_data(test_run, test_case, filename, total_content_extended, num_segments, max_segment, min_segment, avg_segment, 'DPLA', dpla_sim)
                    mysql_obj.insert_stableextension_test_data(test_run, test_case, filename, total_content_extended, num_segments, max_segment, min_segment, avg_segment, 'SIC-DPLA', sic_dpla_sim)
    return []
 
'''      
-- introduce new timbral content (from other files?) between 10-50% of file length, while randomly deleting other content
-------------- params: severe, test_run, file, introduce_content, total_percent_indtroduction, total_percent_deletion, introduction_from_where, num_introduction, num_deletion, max/min/avg introduction and deletion
'''
def run_contentintro_tests(directory, test_run, test_case, mysql_obj):
    total_percent_introduction = random.uniform(10.0, 50.0)                         # percent of file length
    total_percent_deletion = total_percent_introduction*random.uniform(0.8, 1.2)    # delete somewhere in the vicinity of the same amount of content as was introduced 
    # for each file in directory, scale, shift - run through all sim measures - insert each result into db
    if os.path.isdir(directory):
        for dirname, dirnames, filenames in os.walk(directory):
            for filename in filenames:   
                wavefile = re.compile('(.*\.wav$)')
                if wavefile.match(filename):
                    test_audio_file = wave.open(dirname+filename, 'r')
                    # get test audio
                    test_audio = get_audio(test_audio_file)
                    # extract features
                    test_features = get_features(dirname+filename, 'nlse')
                    # distort test audio
                    [content_introduction_audio, file_introduced, num_introduction, max_introduction, min_introduction, avg_introduction, num_deletion, max_deletion, min_deletion, avg_deletion] = introduce_content(test_audio, total_percent_introduction, total_percent_deletion, filter(lambda a: a != filename, filenames), dirname)
                    # save distorted audio
                    distorted_directory = SAVE_DIR + "/" + str(test_run) + "/" + str(test_case)
                    if not os.path.exists(distorted_directory):
                        os.makedirs(distorted_directory)
                    distorted_file = wave.open(distorted_directory + "/" + filename[:-4] + "contentintro.wav", 'w')
                    distorted_file.setparams((1, 2, 44100, content_introduction_audio.shape[0], "NONE", "not compressed"))
                    N = content_introduction_audio.shape[0]
                    shifted_audio = np.asarray(content_introduction_audio.flatten()*(2.0 ** (8 * 2 - 1)), dtype = int)
                    shifted_audio = struct.pack('%dh' % N, * shifted_audio)
                    distorted_file.writeframes(shifted_audio)
                    distorted_file.close()
                    # get distorted features
                    content_introduction_features = get_features(distorted_directory + "/" + filename[:-4] + "contentintro.wav", 'nlse')
                    # calc all similarity values
                    euc_sim = get_similarity(test_features, content_introduction_features, 'euclidean')
                    dtw_sim = get_similarity(test_features, content_introduction_features, 'DTW')
                    dpla_sim = get_similarity(test_features, content_introduction_features, 'DPLA')
                    sic_dpla_sim = get_similarity(test_features, content_introduction_features, 'SIC-DPLA')
                    # store results in db
                    mysql_obj.insert_contentintro_test_data(test_run, test_case, filename, total_percent_introduction, total_percent_deletion, file_introduced, num_introduction, max_introduction, min_introduction, avg_introduction, num_deletion, max_deletion, min_deletion, avg_deletion, 'euclidean', euc_sim)
                    mysql_obj.insert_contentintro_test_data(test_run, test_case, filename, total_percent_introduction, total_percent_deletion, file_introduced, num_introduction, max_introduction, min_introduction, avg_introduction, num_deletion, max_deletion, min_deletion, avg_deletion, 'DTW', dtw_sim)
                    mysql_obj.insert_contentintro_test_data(test_run, test_case, filename, total_percent_introduction, total_percent_deletion, file_introduced, num_introduction, max_introduction, min_introduction, avg_introduction, num_deletion, max_deletion, min_deletion, avg_deletion, 'DPLA', dpla_sim)
                    mysql_obj.insert_contentintro_test_data(test_run, test_case, filename, total_percent_introduction, total_percent_deletion, file_introduced, num_introduction, max_introduction, min_introduction, avg_introduction, num_deletion, max_deletion, min_deletion, avg_deletion, 'SIC-DPLA', sic_dpla_sim)
    return []

'''
-- re-order rand sequences within content (choosing subseqs between 10-20% of file length and swapping out of order up to 5 times)
-------------- params: severe, test_run, file, re-order, number swaps, max_size, min_size, total_size, average_size
'''
def run_reorder_tests(directory, test_run, test_case, mysql_obj):
    num_swaps = random.randint(2, 5)
    # for each file in directory, scale, shift - run through all sim measures - insert each result into db
    if os.path.isdir(directory):
        for dirname, dirnames, filenames in os.walk(directory):
            for filename in filenames:   
                wavefile = re.compile('(.*\.wav$)')
                if wavefile.match(filename):
                    test_audio_file = wave.open(dirname+filename, 'r')
                    # get test audio
                    test_audio = get_audio(test_audio_file)
                    # extract features
                    test_features = get_features(dirname+filename, 'nlse')
                    # distort test audio
                    [reordered_audio, max_size, min_size, total_size, avg_size] = reorder_segments(test_audio, num_swaps)
                    # save distorted audio
                    distorted_directory = SAVE_DIR + "/" + str(test_run) + "/" + str(test_case)
                    if not os.path.exists(distorted_directory):
                        os.makedirs(distorted_directory)
                    distorted_file = wave.open(distorted_directory + "/" + filename[:-4] + "reorder.wav", 'w')
                    distorted_file.setparams((1, 2, 44100, reordered_audio.shape[0], "NONE", "not compressed"))
                    N = reordered_audio.shape[0]
                    shifted_audio = np.asarray(reordered_audio.flatten()*(2.0 ** (8 * 2 - 1)), dtype = int)
                    shifted_audio = struct.pack('%dh' % N, * shifted_audio)
                    distorted_file.writeframes(shifted_audio)
                    distorted_file.close()
                    # get distorted features
                    reordered_features = get_features(distorted_directory + "/" + filename[:-4] + "reorder.wav", 'nlse')
                    # calc all similarity values
                    euc_sim = get_similarity(test_features, reordered_features, 'euclidean')
                    dtw_sim = get_similarity(test_features, reordered_features, 'DTW')
                    dpla_sim = get_similarity(test_features, reordered_features, 'DPLA')
                    sic_dpla_sim = get_similarity(test_features, reordered_features, 'SIC-DPLA')
                    # store results in db
                    mysql_obj.insert_reorder_test_data(test_run, test_case, filename, num_swaps, max_size, min_size, total_size, avg_size, 'euclidean', euc_sim)
                    mysql_obj.insert_reorder_test_data(test_run, test_case, filename, num_swaps, max_size, min_size, total_size, avg_size, 'DTW', dtw_sim)
                    mysql_obj.insert_reorder_test_data(test_run, test_case, filename, num_swaps, max_size, min_size, total_size, avg_size, 'DPLA', dpla_sim)
                    mysql_obj.insert_reorder_test_data(test_run, test_case, filename, num_swaps, max_size, min_size, total_size, avg_size, 'SIC-DPLA', sic_dpla_sim)                    
    return []

'''
-- random insertion of repetitions paired with random deleting of non-repetitive segments (by choosing subseqs between 10-20% file length and repeating up to 3 times)
-------------- params: severe, test_run, file, insert_repetition, number unique repetitions, max_reps for unique, min_reps for unique, total reps, average reps, total_length reps, total_length deletes, num segment deletes, max delete, min delete, max rep length, min rep length, avg_rep_length, avg_delete_length
'''
def run_repinsert_tests(directory, test_run, test_case, mysql_obj):
    num_subsequences = random.randint(2, 3)
    # if greater than 1, determine if they should be same content or not
    # for each file in directory, scale, shift - run through all sim measures - insert each result into db
    if os.path.isdir(directory):
        for dirname, dirnames, filenames in os.walk(directory):
            for filename in filenames:   
                wavefile = re.compile('(.*\.wav$)')
                if wavefile.match(filename):
                    test_audio_file = wave.open(dirname+filename, 'r')
                    # get test audio
                    test_audio = get_audio(test_audio_file)
                    # extract features
                    test_features = get_features(dirname+filename, 'nlse')
                    # distort test audio
                    [repetitive_insertion_audio, num_unique_reps, max_reps_for_unique, min_reps_for_unique, avg_reps, total_length_reps, total_length_deletes, num_segment_deletes, max_delete, min_delete, max_rep_length, min_rep_lenth, avg_rep_length, avg_delete_length] = insert_repetitions(test_audio, num_subsequences)
                    # save distorted audio
                    distorted_directory = SAVE_DIR + "/" + str(test_run) + "/" + str(test_case)
                    if not os.path.exists(distorted_directory):
                        os.makedirs(distorted_directory)
                    distorted_file = wave.open(distorted_directory + "/" + filename[:-4] + "repinsert.wav", 'w')
                    distorted_file.setparams((1, 2, 44100, repetitive_insertion_audio.shape[0], "NONE", "not compressed"))
                    N = repetitive_insertion_audio.shape[0]
                    shifted_audio = np.asarray(repetitive_insertion_audio.flatten()*(2.0 ** (8 * 2 - 1)), dtype = int)
                    shifted_audio = struct.pack('%dh' % N, * shifted_audio)
                    distorted_file.writeframes(shifted_audio)
                    distorted_file.close()
                    # get distorted features
                    repetitive_insert_features = get_features(distorted_directory + "/" + filename[:-4] + "repinsert.wav", 'nlse')
                    # calc all similarity values
                    euc_sim = get_similarity(test_features, repetitive_insert_features, 'euclidean')
                    dtw_sim = get_similarity(test_features, repetitive_insert_features, 'DTW')
                    dpla_sim = get_similarity(test_features, repetitive_insert_features, 'DPLA')
                    sic_dpla_sim = get_similarity(test_features, repetitive_insert_features, 'SIC-DPLA')
                    # store results in db
                    mysql_obj.insert_repinsert_test_data(test_run, test_case, filename, num_subsequences, num_unique_reps, max_reps_for_unique, min_reps_for_unique, avg_reps, total_length_reps, total_length_deletes, num_segment_deletes, max_delete, min_delete, max_rep_length, min_rep_lenth, avg_rep_length, avg_delete_length, 'euclidean', euc_sim)
                    mysql_obj.insert_repinsert_test_data(test_run, test_case, filename, num_subsequences, num_unique_reps, max_reps_for_unique, min_reps_for_unique, avg_reps, total_length_reps, total_length_deletes, num_segment_deletes, max_delete, min_delete, max_rep_length, min_rep_lenth, avg_rep_length, avg_delete_length, 'DTW', dtw_sim)
                    mysql_obj.insert_repinsert_test_data(test_run, test_case, filename, num_subsequences, num_unique_reps, max_reps_for_unique, min_reps_for_unique, avg_reps, total_length_reps, total_length_deletes, num_segment_deletes, max_delete, min_delete, max_rep_length, min_rep_lenth, avg_rep_length, avg_delete_length, 'DPLA', dpla_sim)
                    mysql_obj.insert_repinsert_test_data(test_run, test_case, filename, num_subsequences, num_unique_reps, max_reps_for_unique, min_reps_for_unique, avg_reps, total_length_reps, total_length_deletes, num_segment_deletes, max_delete, min_delete, max_rep_length, min_rep_lenth, avg_rep_length, avg_delete_length, 'SIC-DPLA', sic_dpla_sim)
    return []

if __name__ == "__main__":
    main() 