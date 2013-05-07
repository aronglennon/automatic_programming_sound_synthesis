'''
Created on Apr 14, 2013

@author: apg250
'''
from scikits.samplerate import resample
import random
import sys
import numpy as np

# scale feature list via multi-D resampling
def scale_features(features, scale_percent):
    # constant time warping is the same thing as time stretching. here, we simply resample features since phase is not our concern.  
    # resample SHOULD work since it should just treat each column as a different 'channel' to resample
    return resample(features, scale_percent/100.0, 'sinc_best')

# shift audio by shift_amount samples
def shift_audio(audio, shift_amount):
    # instead of adding zeros, just shift 'backward' in time
    return audio[shift_amount:]

# [time_warped_features, warping_path] = time_warp_features(test_features, min_warping_threshold, max_warping_threshold)
def time_warp_features(features, min_threshold, max_threshold):
    random.seed()
    # generate warping path, which is a random walk given thresholds (TODO: determine exactly the best way to do this)
    # that must move forward - or stall - and end at length of audio
    # movement therefore can be x += 0, x+= 1, x+=2, etc. 
    original_length = len(features)
    # based on rules inserted to make sure min_threhsold is reached if it exists, we need to make sure that is possible given the original_length
    if min_threshold is not None and min_threshold > original_length/2:
        print 'stopping time warp test...min_threshold is too large'
        sys.exit(0)
    # if min_threshold is none, then there is a max threshold
    warp_path = []
    x = 0
    y = 0
    # if min_threshold is none, then there is a max threshold
    if min_threshold is None:
        # create a bias variable that will promote x moves more than y if the warping path is behind and vice versa if it 
        # is ahead
        biasTowardsX = True
        while x < original_length and y < original_length:
            warp_path.append([x,y])
            xMoved = False
            yMoved = False
            '''
             - both x and y move in a random walk forward but can only advance one step at a time
             - also, y is bounded to not be greater than x+max_threshold and not be less than x-max_threshold
             - also, x OR y MUST move and possibly both will - i.e. there must be some progress
            '''
            # first check if x MUST move
            if y == x+max_threshold:
                x += 1
                xMoved = True
                biasTowardsX = True
            # check if y MUST move
            if y == x-max_threshold:
                y += 1
                yMoved = True
                biasTowardsX = False
            # we promote x slightly over y
            if biasTowardsX:
                if not yMoved:
                    if (random.random() <= 0.5):
                        y += 1
                        yMoved = True
                if not xMoved:
                    if not yMoved or (random.random() <= 0.5):
                        x += 1
                        xMoved = True
            # we promote y slightly over x
            else:
            # now, if either of x or y didn't move that means one didn't have to...in this case, flip a coin to see if it does anyway
            # note: it is OK for one to move if the other HAS to, because we'd still keep indices within the max_threshold
                if not xMoved:
                    if (random.random() <= 0.5):
                        x += 1
                        xMoved = True
                if not yMoved:
                    # if x still hasn't moved even after coin flip, y has to move...otherwise, y also has a coin flip
                    if not xMoved or (random.random() <= 0.5):
                        y += 1
                        yMoved = True
        # after while, if either x or y are not original_length, add index pairs until both indices reach original_length - 1
        while x < original_length - 1:
            x += 1
            warp_path.append([x, y-1])
        # this cannot run if the above while loop does since one of x and y had to have been original_length
        while y < original_length - 1:
            y += 1
            warp_path.append([x-1, y])
    # if max_threshold is none, then there is a min_threshold
    else:
        # create a bias variable that will promote x moves more than y if the warping path is behind and vice versa if it 
        # is ahead
        biasTowardsX = True
        while x < original_length and y < original_length:
            warp_path.append(x,y)
            xMoved = False
            yMoved = False
            '''
            With a min threshold, we simply have to make sure that we at least move past the min_threshold. To make this simple
            we push forward y to make it to min_threshold within the first half of x's length.
            
             - both x and y move in a random walk forward but can only advance one step at a time
             - also, y is bounded to not be less than x+max_threshold or greater than x+max_threshold
             - also, x OR y MUST move and possibly both will - i.e. there must be some progress
            '''
            # check if x < original_length/2
            if x <= original_length/2 and y-x < min_threshold:
                '''
                 we want  ahigh prob that y is moved so it can get to min_threshold
                 specifically we would like y to outpace x by 'roughly' min_threshold over original_length/2
                 thus, we want x to have taken original_length/2 steps and y original_length/2 + min_threshold steps
                 the math would be dirt simple if EITHER x OR y moved on each iteration, but we have a probability of both
                 moving. If we want to keep the prob of a diagonal move the same, we simply require prob_y * prob_x = 0.5^2=0.25.
                 In other words, we want 25% of all iterations to produce a move in y and x. This would mean around (original_length+min_threshold)*0.25.
                 Let's call this M iterations. If y needs to get to y original_length/2 + min_threshold and x to original_length/2 and we have M iterations
                 where both move, then the total number of iterations will be original_length+min_threshold-M.
                 The prob of y movement would then need to be (original_length/2+min_threshold) / (original_length+min_threshold-M)
                '''
                prob_y = (original_length/2+min_threshold) / 0.75*(original_length+min_threshold)
                '''
                 since the prob of x moving * prob of y moving is M/((original_length+min_threshold-M)) and the prob of y moving is above,
                 the prob of x moving should be M / (original_length/2+min_threshold)
                '''
                prob_x = ((original_length+min_threshold)*0.25) / (original_length/2+min_threshold)
                if (random.random() < prob_y):
                    y +=1
                    yMoved = True
                if not yMoved or (random.random() <= prob_x):
                    x += 1
                    xMoved = True
            # if we make it to original_length/2 and the distance is still not great enough, push y forward until it is
            elif x > original_length/2 and y-x < min_threshold:
                y += 1
            # we are passed the original_length/2 point for x AND we have met our min_threshold goal...now we just need to allow
            # both x and y to move forward naturally, with bias changing based on which is ahead
            else:
                # slight bias towards x moves
                if biasTowardsX:
                    if (random.random() <= 0.5):
                        y += 1
                        yMoved = True
                    if not yMoved or (random.random() <= 0.5):
                        x += 1
                        xMoved = True
                    # change bias is we get all the way to a negative min_threshold separating x and y
                    if x - y > min_threshold:
                        biasTowardsX = False
                # slight bias towards y moves
                else:
                    if (random.random() <= 0.5):
                        x += 1
                        xMoved = True
                    if not xMoved or (random.random() <= 0.5):
                        y += 1
                        yMoved = True
                    if y - x > min_threshold:
                        biasTowardsX = True
        # after while, if either x or y are not original_length, add index pairs until both indices reach original_length - 1
        while x < original_length - 1:
            x += 1
            warp_path.append([x, y-1])
        # this cannot run if the above while loop does since one of x and y had to have been original_length
        while y < original_length - 1:
            y += 1
            warp_path.append([x-1, y])
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