'''
Created on Apr 14, 2013

@author: apg250
'''
from scikits.samplerate import resample

# scaled_audio = scale_audio(test_audio, scale_percent)
def scale_audio(audio, scale_percent):
    # constant time warping is the same thing as resampling   
    return resample(audio, scale_percent/100.0, 'sinc_best')

# scaled_and_shifted_audio = shift_audio(scaled_audio, shift_amount)
def shift_audio(audio, shift_amount):
    # instead of adding zeros, just shift 'backward' in time
    return audio[shift_amount:]

# [time_warped_audio, warping_path] = time_warp_audio(test_audio, min_warping_threshold, max_warping_threshold)
def time_warp_audio(audio, min_threshold, max_threshold):
    return []

# [deleted_sample_audio, num_segments, max_segment, min_segment, avg_segment] = delete_samples(test_audio, total_deleted_content)
def delete_samples(audio, total_percent_to_delete):
    return []

# [stable_extension_audio, num_segments, max_segment, min_segment, avg_segment] = stable_extension(test_audio, total_content_extended)
def stable_extension(audio, total_percent_to_extended):
    return []

# [content_introduction_audio, file_introduced, num_introduction, max_introduction, min_introduction, avg_introduction, num_deletion, max_deletion, min_deletion, avg_deletion] = introduce_content(test_audio, total_percent_introduction, total_percent_deletion, directory)
def introduce_content(audio, total_percent_introduction, total_percent_deletion, directory):
    return  []

# [reordered_audio, max_size, min_size, total_size, avg_size] = reorder_segments(test_audio, num_swaps)
def reorder_segments(audio, num_swaps):
    return []

# [repetitive_insertion_audio, num_unique_reps, max_reps_for_unique, avg_reps, total_length_reps, total_length_deletes, num_segment_deletes, max_delete, min_delete, max_rep_length, min_rep_lenth, avg_rep_length, avg_delete_length] = insert_repetitions(test_audio, num_reps)
def insert_repetitions(audio, num_reps):
    return []