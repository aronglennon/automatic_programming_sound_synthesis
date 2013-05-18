'''
Created on Apr 14, 2013

@author: apg250
'''
from scikits.samplerate import resample
import random
import sys
import numpy as np
import wave
from features.features_functions import get_audio

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
    # now that warping path is created, step through to create 'y'
    y = 0
    time_warped_features = [features[0]]
    for w in warp_path:
        # if the y coordinate is not stalled, add it to the time_warped_features
        if w[1] != y:
            time_warped_features.append(features[w[1]])
    return time_warped_features, warp_path

# [deleted_sample_audio, num_segments, max_segment, min_segment, avg_segment] = delete_samples(test_audio, total_deleted_content)
def delete_samples(audio, total_percent_to_delete):
    distorted_audio = []
    num_segments = random.randint(1,10)
    amount_to_delete = round(len(audio)*total_percent_to_delete)
    avg_segment = round(amount_to_delete/num_segments)
    # using length, choose random segments to delete, jumping forward 'around' 1/num_segments and deleting 'around' avg_segment
    avg_jump = round(len(audio)/num_segments)
    current_position = 0
    # first delete amount
    rand_delete_amount = random.randint(0,avg_segment)
    # simply by jumping current position forward, we are 'deleting' samples
    current_position += rand_delete_amount
    # start accumulating the total delete amount
    total_delete_amount = rand_delete_amount
    # setup max and min segment amounts
    max_segment = rand_delete_amount
    min_segment = rand_delete_amount
    for i in range(1, num_segments-2):
        # jump random distance, but no more than where this jump would end if this was deterministic
        jump_size = random.randint(0,avg_jump*(i)-current_position)
        distorted_audio.append(audio[current_position:current_position+jump_size])
        current_position += jump_size
        # do not add the following audio up to rand_delete_amount
        rand_delete_amount = random.randint(0,avg_segment*(i)-total_delete_amount)
        current_position += rand_delete_amount
        total_delete_amount += rand_delete_amount
        # update max and min if necessary
        if rand_delete_amount < min_segment:
            min_segment = rand_delete_amount
        if rand_delete_amount > max_segment:
            max_segment = rand_delete_amount
    # ...at the end, make sure last segment can delete what is necessary AND make sure avg_segment is maintained
    rand_delete_amount = amount_to_delete - total_delete_amount
    if rand_delete_amount < min_segment:
        min_segment = rand_delete_amount
    if rand_delete_amount > max_segment:
        max_segment = rand_delete_amount
    current_position += rand_delete_amount
    distorted_audio.append(audio[current_position:])    
    return distorted_audio, num_segments, max_segment, min_segment, avg_segment

# [stable_extension_audio, num_segments, max_segment, min_segment, avg_segment] = stable_extension(test_audio, total_content_extended)
def stable_extension(audio, total_percent_to_extended):
    stable_extension_audio = []
    # we don't extend anything beyond 250ms b.c. some of the files used are time-varying at around 1 Hz and we don't want to create
    # timbre pattern repetitions
    largest_length = 44100/4.0
    avg_segment = largest_length/2.0
    amount_to_extend = round(len(audio)*total_percent_to_extended)
    num_segments = round(amount_to_extend/avg_segment)
    avg_jump = round(len(audio)/num_segments)
    current_position = 0
    total_extension_amount = 0    
    max_segment = 0
    min_segment = len(audio)
    for i in range(0, num_segments-2):
        start_extension = random.randint(0,avg_jump*(i+1)-current_position) + current_position
        rand_extension_amount = random.randint(0,avg_segment*(i+1)-total_extension_amount)
        end_extension = start_extension + rand_extension_amount
        total_extension_amount += rand_extension_amount
        # copy over audio up to end of first extension, then repeat extension part
        stable_extension_audio.append(audio[current_position:end_extension])
        stable_extension_audio.append(audio[start_extension:end_extension])
        # mark current_position as where we left off
        current_position = end_extension
        # update max and min if necessary
        if rand_extension_amount < min_segment:
            min_segment = rand_extension_amount
        if rand_extension_amount > max_segment:
            max_segment = rand_extension_amount
    # copy over end
    start_extension = random.randint(0,avg_jump*(i+1)-current_position) + current_position
    rand_extension_amount = amount_to_extend - total_extension_amount
    end_extension = start_extension + rand_extension_amount
    stable_extension_audio.append(audio[current_position:end_extension])
    # update max and min if necessary
    if rand_extension_amount < min_segment:
        min_segment = rand_extension_amount
    if rand_extension_amount > max_segment:
        max_segment = rand_extension_amount
    # copy all the way to the end after the extension
    stable_extension_audio.append(audio[start_extension:])
    return stable_extension_audio, num_segments, max_segment, min_segment, avg_segment

# [content_introduction_audio, file_introduced, num_introduction, max_introduction, min_introduction, avg_introduction, num_deletion, max_deletion, min_deletion, avg_deletion] = introduce_content(test_audio, total_percent_introduction, total_percent_deletion, directory)
def introduce_content(audio, total_percent_introduction, total_percent_deletion, filenames):
    # choose random file from directory
    rand_index = random.randint(0,len(filenames)-1)
    chosen_file = filenames[rand_index]
    chosen_file_wave = wave.open(chosen_file, 'r')
    # get audio
    chosen_file_audio = get_audio(chosen_file_wave)
    # given percent introduction, determine size of total introduction and of avg introduction, follow steps as in delete_samples
    # follow steps in delete_samples for deletion
    
    deleted_audio = []
    '''
    FIRST DELETE
    '''
    num_deletion = random.randint(1,10)
    amount_to_delete = round(len(audio)*total_percent_deletion)
    avg_deletion = round(amount_to_delete/num_deletion)
    # using length, choose random segments to delete, jumping forward 'around' 1/num_segments and deleting 'around' avg_segment
    avg_jump = round(len(audio)/num_deletion)
    current_position = 0
    # first delete amount
    rand_delete_amount = random.randint(0,avg_deletion)
    # simply by jumping current position forward, we are 'deleting' samples
    current_position += rand_delete_amount
    # start accumulating the total delete amount
    total_delete_amount = rand_delete_amount
    # setup max and min segment amounts
    max_deletion = rand_delete_amount
    min_deletion = rand_delete_amount
    for i in range(1, num_deletion-2):
        # jump random distance, but no more than where this jump would end if this was deterministic
        jump_size = random.randint(0,avg_jump*(i)-current_position)
        deleted_audio.append(audio[current_position:current_position+jump_size])
        current_position += jump_size
        # do not add the following audio up to rand_delete_amount
        rand_delete_amount = random.randint(0,avg_deletion*(i)-total_delete_amount)
        current_position += rand_delete_amount
        total_delete_amount += rand_delete_amount
        # update max and min if necessary
        if rand_delete_amount < min_deletion:
            min_deletion = rand_delete_amount
        if rand_delete_amount > max_deletion:
            max_deletion = rand_delete_amount
    # ...at the end, make sure last segment can delete what is necessary AND make sure avg_segment is maintained
    rand_delete_amount = amount_to_delete - total_delete_amount
    if rand_delete_amount < min_deletion:
        min_deletion = rand_delete_amount
    if rand_delete_amount > max_deletion:
        max_deletion = rand_delete_amount
    current_position += rand_delete_amount
    deleted_audio.append(audio[current_position:])    
    '''
    THEN INTRODUCE
    '''
    content_introduction_audio = []
    largest_length = 44100/4.0
    avg_introduction = largest_length/2.0
    amount_to_introduce = round(len(audio)*total_percent_introduction)
    num_introduction = round(amount_to_introduce/avg_introduction)
    avg_jump = round(len(audio)/num_introduction)
    current_position = 0
    total_introduction_amount = 0    
    max_introduction = 0
    min_introduction = len(audio)
    for i in range(0, num_introduction-2):
        start_introduction = random.randint(0,avg_jump*(i+1)-current_position) + current_position
        rand_introduction_amount = random.randint(0,avg_introduction*(i+1)-total_introduction_amount)
        total_introduction_amount += rand_introduction_amount
        # copy over audio up to end of first introduction, then introduce audio
        content_introduction_audio.append(deleted_audio[current_position:start_introduction])
        intro_start = random.randint(0, len(chosen_file_audio)-rand_introduction_amount-1)
        content_introduction_audio.append(chosen_file_audio[intro_start:(intro_start+rand_introduction_amount)])
        # mark current_position as where we left off
        current_position = start_introduction
        # update max and min if necessary
        if rand_introduction_amount < min_introduction:
            min_introduction = rand_introduction_amount
        if rand_introduction_amount > max_introduction:
            max_introduction = rand_introduction_amount
    # introduce based on what is left
    start_introduction = random.randint(0,avg_jump*(i+1)-current_position) + current_position
    rand_introduction_amount = amount_to_introduce - total_introduction_amount
    content_introduction_audio.append(deleted_audio[current_position:start_introduction])
    intro_start = random.randint(0, len(chosen_file_audio)-rand_introduction_amount-1)
    content_introduction_audio.append(chosen_file_audio[intro_start:(intro_start+rand_introduction_amount)])
    # update max and min if necessary
    if rand_introduction_amount < min_introduction:
        min_introduction = rand_introduction_amount
    if rand_introduction_amount > max_introduction:
        max_introduction = rand_introduction_amount
    # copy all the way to the end after the introduction
    content_introduction_audio.append(chosen_file_audio[start_introduction:])
    return content_introduction_audio, chosen_file, num_introduction, max_introduction, min_introduction, avg_introduction, num_deletion, max_deletion, min_deletion, avg_deletion

# [reordered_audio, max_size, min_size, total_size, avg_size] = reorder_segments(test_audio, num_swaps)
def reorder_segments(audio, num_swaps):
    reordered_audio = []
    # swap amount between 10%-20% of file length
    random_swap = random.randint(len(audio)*0.10, len(audio)*0.20)
    min_swap = random_swap
    max_swap = random_swap
    total_swap = random_swap
    # choose swap locations that do not overlap (simplest way is to choose first location in first half of audio and second in second)
    location_one = random.randint(0,len(audio)/2-random_swap)
    location_two = random.randint(len(audio)/2, len(audio)-random_swap)
    location_one_audio = audio[location_one:(location_one+random_swap)]
    location_two_audio = audio[location_two:(location_two+random_swap)]
    audio[location_one:(location_one+random_swap)]= location_two_audio
    audio[location_two:(location_two+random_swap)] = location_one_audio
    for i in range(1, num_swaps-1):
        random_swap = random.randint(len(audio)*0.10, len(audio)*0.20)
        if random_swap < min_swap:
            min_swap = random_swap
        if random_swap > max_swap:
            max_swap = random_swap
        total_swap += random_swap
        # choose swap locations that do not overlap (simplest way is to choose first location in first half of audio and second in second)
        location_one = random.randint(0,len(audio)/2-random_swap)
        location_two = random.randint(len(audio)/2, len(audio)-random_swap)
        location_one_audio = audio[location_one:(location_one+random_swap)]
    location_two_audio = audio[location_two:(location_two+random_swap)]
    audio[location_one:(location_one+random_swap)]= location_two_audio
    audio[location_two:(location_two+random_swap)] = location_one_audio
    average_swap_size = total_swap/num_swaps
    return reordered_audio, max_swap, min_swap, total_swap, average_swap_size

# [repetitive_insertion_audio, num_unique_reps, max_reps_for_unique, avg_reps, total_length_reps, total_length_deletes, num_segment_deletes, max_delete, min_delete, max_rep_length, min_rep_lenth, avg_rep_length, avg_delete_length] = insert_repetitions(test_audio, num_subsequences)
def insert_repetitions(audio, num_subsequences):
    repetitive_insertion_audio = []
    swaps = []
    num_unique_reps = num_subsequences
    total_length_reps = 0
    sum_unique_rep_lengths = 0
    total_reps = 0
    max_reps_for_unique = 1
    max_rep_length = 0
    min_rep_length = len(audio)
    for i in range(0, num_subsequences-1):
        num_reps = random.randint(1, 3)
        total_reps += num_reps
        if num_reps > max_reps_for_unique:
            max_reps_for_unique = num_reps
        random_rep_length = random.randint(len(audio)*0.10, len(audio)*0.20)
        if random_rep_length > max_rep_length:
            max_rep_length = random_rep_length
        if random_rep_length < min_rep_length:
            min_rep_length = random_rep_length
        swaps.append([num_reps, random_rep_length])
        total_length_reps += num_reps*random_rep_length
        sum_unique_rep_lengths += random_rep_length
    avg_reps = total_reps / num_subsequences
    avg_rep_length = sum_unique_rep_lengths / num_subsequences
    
    '''
    FIRST DELETE
    '''
    deleted_audio = []
    amount_to_delete = random.randint(total_length_reps*0.8, total_length_reps*1.2)
    num_segment_deletes = random.randint(1,10)
    avg_delete_length = round(amount_to_delete/num_segment_deletes)
    # using length, choose random segments to delete, jumping forward 'around' 1/num_segments and deleting 'around' avg_segment
    avg_jump = round(len(audio)/num_segment_deletes)
    current_position = 0
    # first delete amount
    rand_delete_amount = random.randint(0,avg_delete_length)
    # simply by jumping current position forward, we are 'deleting' samples
    current_position += rand_delete_amount
    # start accumulating the total delete amount
    total_length_deletes = rand_delete_amount
    # setup max and min segment amounts
    max_delete = rand_delete_amount
    min_delete = rand_delete_amount
    for i in range(1, num_segment_deletes-2):
        # jump random distance, but no more than where this jump would end if this was deterministic
        jump_size = random.randint(0,avg_jump*(i)-current_position)
        deleted_audio.append(audio[current_position:current_position+jump_size])
        current_position += jump_size
        # do not add the following audio up to rand_delete_amount
        rand_delete_amount = random.randint(0,avg_delete_length*(i)-total_length_deletes)
        current_position += rand_delete_amount
        total_length_deletes += rand_delete_amount
        # update max and min if necessary
        if rand_delete_amount < min_delete:
            min_delete = rand_delete_amount
        if rand_delete_amount > max_delete:
            max_delete = rand_delete_amount
    # ...at the end, make sure last segment can delete what is necessary AND make sure avg_segment is maintained
    rand_delete_amount = amount_to_delete - total_length_deletes
    if rand_delete_amount < min_delete:
        min_delete = rand_delete_amount
    if rand_delete_amount > max_delete:
        max_delete = rand_delete_amount
    current_position += rand_delete_amount
    deleted_audio.append(audio[current_position:])  
    
    '''
    THEN REPEAT
    '''
    avg_jump = round(len(deleted_audio/num_subsequences))
    current_position = 0
    total_extension_amount = 0    
    # swaps -> [num_reps, random_rep_length]
    jump = 0
    for s in swaps:
        start_repetition = random.randint(0,avg_jump*jump-current_position) + current_position
        end_repetition = start_repetition + s[1]
        # copy over audio up to end of first extension, then repeat extension part
        repetitive_insertion_audio.append(audio[current_position:end_repetition])
        # repeat as many times as necessary
        for i in range(0, s[0]-1):
            repetitive_insertion_audio.append(audio[start_repetition:end_repetition])
        # mark current_position as where we left off
        current_position = end_repetition
    # copy all the way to the end after the extension
    repetitive_insertion_audio.append(audio[current_position:])
    return repetitive_insertion_audio, num_unique_reps, max_reps_for_unique, avg_reps, total_length_reps, total_length_deletes, num_segment_deletes, max_delete, min_delete, max_rep_length, min_rep_length, avg_rep_length, avg_delete_length
