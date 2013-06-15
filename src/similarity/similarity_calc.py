import numpy as np

import rpy2.robjects.numpy2ri
from rpy2.robjects.packages import importr
from features.features_functions import get_features

rpy2.robjects.numpy2ri.activate()
# Set up our R namespaces
R = rpy2.robjects.r
DTW = importr('dtw')
from matplotlib import pylab as pl

def get_similarity(features1, features2, similarity_type):
    print 'calculating similarity'
    # option 1: calculate euclidean distance and send back multiplicative inverse so that a larger distance has lower fitness
    if similarity_type == 'euclidean':
        return 1.0 - get_euclidean(features1, features2)
    # option 2: use DTW - no path constraints, local continuity constraint in place, global alignment, Euclidean distance
    elif similarity_type == 'DTW':
        return 1.0 - get_DTW_dist(features1, features2)
    # option 3 : DPLA
    elif similarity_type == 'DPLA':
        return get_DPLA(features1, features2)
    # option 4: SIC-DPLA
    elif similarity_type == 'SIC-DPLA':
        return get_SIC_DPLA(features1, features2)

def get_euclidean(features1, features2):
    # make sure both matrices are the same size...if not truncate the larger one
    dist = 0.0
    if len(features1) > len(features2):
        trunc_features1 = features1[:len(features2)]
        for i in range(0, features2.shape[0]):
            # the nlse features are in 3-space with [-1.0, 1.0] ranges in each dim, so the max distance is sqrt(12) or 2*sqrt(3)...we divide by this to normalize between 0.0 and 1.0
            dist += np.linalg.norm(trunc_features1[i][:]-features2[i][:]) / (2*np.sqrt(3.0))
        # normalize over sum of distances
        dist /= float(features2.shape[0])
        return dist
    elif len(features1) < len(features2):
        trunc_features2 = features2[:len(features1)]
        for i in range(0, features1.shape[0]):
            dist += np.linalg.norm(features1[i][:]-trunc_features2[i][:]) / (2*np.sqrt(3.0))   
        # normalize over sum of distances
        dist /= float(features1.shape[0])
        return dist
    else:
        for i in range(0, features1.shape[0]):
            dist += np.linalg.norm(features1[i][:]-features2[i][:]) / (2*np.sqrt(3.0))
        # normalize over sum of distances
        dist /= float(features1.shape[0])
        return dist

# TODO: look into other options and what default is if we don't specify them
def get_DTW_dist(features1, features2):
    alignment = R.dtw(features1, features2, keep=True)
    return alignment.rx('normalizedDistance')[0][0]

# TODO: Calculate beginning of SIC_DPLA
def get_DPLA(features1, features2):
    max_sequence_length = max(len(features1), len(features2))
    # create similarity matrix as input to Smith Waterman
    similarity_matrix = np.zeros(shape=(len(features1),len(features2)))
    for i in range(0, len(features1)):
        for j in range(0, len(features2)):
            # calculate similarity as transformed version of Euclidean distance to fit between -1.0 and 1.0
            similarity_matrix[i][j] = 1.0 - (np.linalg.norm(features1[i][:]-features2[j][:]))/np.sqrt(3.0)
    # generate Smith-Waterman H matrix
    alignment_matrix = np.zeros(shape=(len(features1),len(features2)))
    # generate corresponding path matrix P (to track the alignment path to any index i,j)
    path_trace_matrix = np.empty(shape=(len(features1),len(features2)), dtype=object)
    # generate corresponding warp extension matrix (to track how far a warping is being extended)
    warp_extension_matrix = np.zeros(shape=(len(features1),len(features2)))
    # each element is generated with info from elements to its left, diagonal-down-left, and below it AND
    # elements in the similarity matrix from its diagonal-down-left, left, and below
    # --- calculate first elements
    for i in range(0, len(features1)):
        # j is zero
        alignment_matrix[i][0] = max(similarity_matrix[i][0], 0)
        path_trace_matrix[i][0] = [-1,-1]
    for j in range(1, len(features2)):
        # i is zero
        alignment_matrix[0][j] = max(similarity_matrix[0][j], 0)
        path_trace_matrix[0][j] = [-1,-1]
    # --- calculate the rest of the matrices
    for i in range(1, len(features1)):
        for j in range(1, len(features2)):
            diagonal = alignment_matrix[i-1][j-1]+similarity_matrix[i][j]
            left = alignment_matrix[i][j-1]+similarity_matrix[i][j] - delta(warp_extension_matrix[i][j-1], max_sequence_length)
            right = alignment_matrix[i-1][j]+similarity_matrix[i][j] - delta(warp_extension_matrix[i-1][j], max_sequence_length)
            alignment_matrix[i][j] = max(diagonal, left, right, 0)
            max_index = [diagonal, left, right, 0].index(alignment_matrix[i][j])
            # diagonal was chosen
            if max_index == 0:
                warp_extension_matrix[i][j] = 0
                path_trace_matrix[i][j] = [i-1,j-1]
            # left was chosen
            elif max_index == 1:
                warp_extension_matrix[i][j] = warp_extension_matrix[i][j-1] + 1
                path_trace_matrix[i][j] = [i,j-1]
            # right was chosen
            elif max_index == 2:
                warp_extension_matrix[i][j] = warp_extension_matrix[i-1][j] + 1
                path_trace_matrix[i][j] = [i-1,j]
            # zero was chosen (meaning no alignment path is allowed)
            else:
                warp_extension_matrix[i][j] = 0
                # sentinel meaning (not traceable - i.e. if you reach this, it is the start of a local alignment)
                path_trace_matrix[i][j] = [-1,-1] 
    # return similarity value as 1.0 / DPLA dissimilarity value
    return 1.0/DPLA(alignment_matrix, len(features1), len(features2))

def DPLA(alignment_matrix, superior_length, inferior_length):    
    # find max in Smith-Waterman matrix and divide sum of lengths by it to get 'dissimilarity' score
    max_value = np.max(alignment_matrix)
    max_length = max(inferior_length, superior_length)
    return max_length/max_value

def get_SIC_DPLA(features1, features2):
    max_sequence_length = max(len(features1), len(features2))
    # create similarity matrix as input to Smith Waterman
    similarity_matrix = np.zeros(shape=(len(features1),len(features2)))
    for i in range(0, len(features1)):
        for j in range(0, len(features2)):
            # calculate similarity as transformed version of Euclidean distance to fit between -1.0 and 1.0
            similarity_matrix[i][j] = 1.0 - (np.linalg.norm(features1[i][:]-features2[j][:]))/np.sqrt(3.0)
    # generate Smith-Waterman H matrix
    alignment_matrix = np.zeros(shape=(len(features1),len(features2)))
    # generate corresponding path matrix P (to track the alignment path to any index i,j)
    path_trace_matrix = np.empty(shape=(len(features1),len(features2)), dtype=object)
    # generate corresponding warp extension matrix (to track how far a warping is being extended)
    warp_extension_matrix = np.zeros(shape=(len(features1),len(features2)))
    # each element is generated with info from elements to its left, diagonal-down-left, and below it AND
    # elements in the similarity matrix from its diagonal-down-left, left, and below
    # --- calculate first elements
    for i in range(0, len(features1)):
        # j is zero
        alignment_matrix[i][0] = max(similarity_matrix[i][0], 0)
        path_trace_matrix[i][0] = [-1,-1]
    for j in range(1, len(features2)):
        # i is zero
        alignment_matrix[0][j] = max(similarity_matrix[0][j], 0)
        path_trace_matrix[0][j] = [-1,-1]
    # --- calculate the rest of the matrices
    for i in range(1, len(features1)):
        for j in range(1, len(features2)):
            diagonal = alignment_matrix[i-1][j-1]+similarity_matrix[i][j]
            left = alignment_matrix[i][j-1]+similarity_matrix[i][j] - delta(warp_extension_matrix[i][j-1], max_sequence_length)
            right = alignment_matrix[i-1][j]+similarity_matrix[i][j] - delta(warp_extension_matrix[i-1][j], max_sequence_length)
            alignment_matrix[i][j] = max(diagonal, left, right, 0)
            max_index = [diagonal, left, right, 0].index(alignment_matrix[i][j])
            # diagonal was chosen
            if max_index == 0:
                warp_extension_matrix[i][j] = 0
                path_trace_matrix[i][j] = [i-1,j-1]
            # left was chosen
            elif max_index == 1:
                warp_extension_matrix[i][j] = warp_extension_matrix[i][j-1] + 1
                path_trace_matrix[i][j] = [i,j-1]
            # right was chosen
            elif max_index == 2:
                warp_extension_matrix[i][j] = warp_extension_matrix[i-1][j] + 1
                path_trace_matrix[i][j] = [i-1,j]
            # zero was chosen (meaning no alignment path is allowed)
            else:
                warp_extension_matrix[i][j] = 0
                # sentinel meaning (not traceable - i.e. if you reach this, it is the start of a local alignment)
                path_trace_matrix[i][j] = [-1,-1] 
    # preliminary IC-DPLA in one direction
    [ICDPLA_left_prelim, alignments_left] = ICDPLA(alignment_matrix, path_trace_matrix, features1, features2, 0)
    # calc penalties
    [p_swap_left, sorted_alignments_left] = calc_p_swap(alignments_left)
    [p_overlap_gap_left, num_repetitions] = calc_p_overlap_gap(sorted_alignments_left, len(features2))
    p_repetitions_left = float(num_repetitions + len(alignments_left))/ len(alignments_left)
    penalties_left = p_swap_left * p_overlap_gap_left * p_repetitions_left
    # preliminary IC-DPLA in opposite direction
    [ICDPLA_right_prelim, alignments_right] = ICDPLA(alignment_matrix.transpose(), path_trace_matrix.transpose(), features2, features1, 0, True)
    # calc penalties
    [p_swap_right, sorted_alignments_right] = calc_p_swap(alignments_right)
    [p_overlap_gap_right, num_repetitions] = calc_p_overlap_gap(sorted_alignments_right, len(features1))
    p_repetitions_right = float(num_repetitions + len(alignments_right))/ len(alignments_right)
    penalties_right = p_swap_right * p_overlap_gap_right * p_repetitions_right
    # calc penalizes IC-DPLAs
    ICDPLA_left = penalties_left * ICDPLA_left_prelim
    ICDPLA_right = penalties_right * ICDPLA_right_prelim
    # return SIC-DPLA similarity
    return 1.0 - (ICDPLA_left/features1.shape[0] + ICDPLA_right/features2.shape[0])/2.0

# this takes a presorted alignments list
def calc_p_overlap_gap(presorted_alignments, inferior_sequence_length):
    # loop vars
    gap_length = 0
    overlap_length = 0
    num_repetitions = 0
    current_location_in_sequence = 0
    current_alignment_start = 0
    current_alignment_end = 0
    previous_alignment_start = 0
    previous_alignment_end = 0
    for p in presorted_alignments:
        current_alignment_start = p[0][1]
        current_alignment_end = p[1][1]
        # if we are starting beyond what we've seen alignments up to, there is a gap
        if current_alignment_start > current_location_in_sequence:
            gap_length += (current_alignment_start - current_location_in_sequence)
            current_location_in_sequence = current_alignment_start
        # check for overlaps or repetitions by looking if any overlap exists with last alignment
        if current_alignment_start < previous_alignment_end:
            # the following will only be checked if necessary
            overlap = previous_alignment_end - current_alignment_start
            # check to make sure entire alignment is not enclosed within previous
            if current_alignment_end < previous_alignment_end:
                # this is completely enclosed in last alignment
                num_repetitions += 1
                # NOTE: no need to update current location in sequence given that last alignment went further
            # check if previous is enclosed by this
            elif current_alignment_start == previous_alignment_start and current_alignment_end >= previous_alignment_end:
                num_repetitions += 1
                current_location_in_sequence = current_alignment_end
            # check if overlap is greater than half of either this or last subsequence
            elif overlap >= (previous_alignment_end-previous_alignment_start)/2.0 or overlap >= (current_alignment_end-current_alignment_start)/2.0:
                # mark as repetition
                num_repetitions += 1
                current_location_in_sequence = current_alignment_end
            # entire alignment not enclosed in previous, nor previous in this, the overlap amount is not larger than half of either alignment
            else:
                overlap_length += overlap
                current_location_in_sequence = current_alignment_end
        previous_alignment_start = current_alignment_start
        # previous alignment end should be the greatest of all values thus far, so that the overlap of next alignment shows overlap over all accumulated segments up to it
        # this is why we also extend even if there is a repetition, so that we close gaps that would be introduced once the repetition is removed
        if current_location_in_sequence > previous_alignment_end:
            previous_alignment_end = current_location_in_sequence
    p_overlap_gap = float(inferior_sequence_length + gap_length + overlap_length) / inferior_sequence_length
    return p_overlap_gap, num_repetitions

def calc_p_swap(alignments):
    if len(alignments) == 1:
        return 1.0, alignments
    else:
        [num_swaps, alignments_to_swap] = select_sort(alignments)
        p_swap = float(num_swaps + len(alignments_to_swap)) / len(alignments_to_swap)
        return p_swap, alignments_to_swap

def select_sort(alignments):
    num_swaps = 0
    # determine the min number of swaps using selection-sort-like swapping
    # NOTE: if two alignments start in the same y coord, we accept any ordering of them
    alignments_to_swap = alignments
    for i in range(0,len(alignments_to_swap)):
        # assume this index is the min
        min_index = i
        # search for new min
        for j in range (i+1, len(alignments_to_swap)):
            if alignments_to_swap[j][0][1] < alignments_to_swap[min_index][0][1]:
                min_index = j
        # if we find a new min, swap
        if min_index != i:
            temp = alignments_to_swap[min_index]
            alignments_to_swap[min_index] = alignments_to_swap[i]
            alignments_to_swap[i] = temp
            num_swaps += 1
    return num_swaps, alignments_to_swap

def ICDPLA(alignment_matrix, path_trace_matrix, superior, inferior, row_offset, transposed=False):
    # stopping condition -> if max value is 0, there are no more alignments..or the matrix is empty, so just return nothing 
    if len(alignment_matrix) == 0 or (np.max(alignment_matrix) == 0):
        return 0, []
    # find max in Smith-Waterman matrix
    max_index = pl.unravel_index(alignment_matrix.argmax(), alignment_matrix.shape)
    # calculate distance over alignment path
    local_distance = 0.0
    # the start index will be where the alignment begins (necessary to remove submatrix)
    start_x = row_offset
    start_y = 0
    # these indices trace path backwards
    x_index = max_index[0]+row_offset
    y_index = max_index[1]
    while (x_index != -1 and x_index >= row_offset):
        start_x = x_index
        start_y = y_index
        local_distance += (np.linalg.norm(superior[x_index][:]-inferior[y_index][:]))/(2*np.sqrt(3))
        if transposed:
            [y_index, x_index] = path_trace_matrix[x_index][y_index]
        else:
            [x_index, y_index] = path_trace_matrix[x_index][y_index]
    # remove appropriate rows from sequence1 and split into two matrices to be involved in the same process
    alignment_top_submatrix = alignment_matrix[:(start_x-row_offset),:]
    alignment_bottom_submatrix = alignment_matrix[max_index[0]+1:, :]
    [distance_top, alignments_top] = ICDPLA(alignment_top_submatrix, path_trace_matrix, superior, inferior, row_offset, transposed)
    [distance_bottom, alignments_bottom] = ICDPLA(alignment_bottom_submatrix, path_trace_matrix, superior, inferior, row_offset+max_index[0], transposed)
    total_distance = distance_top+distance_bottom+local_distance
    alignments = [[[start_x, start_y], [max_index[0]+row_offset, max_index[1]]]]
    alignments.extend(alignments_top)
    alignments.extend(alignments_bottom)
    return total_distance, alignments
    
# warping penalty - note that this is before the length is increased at i,j, which is appropriate, because
# this formula assumes a warping opening has a length of 0
def delta(warp_length, max_sequence_length):
    return 0.5*(1.0 + warp_length/max_sequence_length)

def main():
    FILENAMES = ['/Users/apg250/git/automatic_programming_sound_synthesis/max_patches/realworld_sounds/for_testing/Metal_Gong-Mono.wav', 
                 '/Users/apg250/git/automatic_programming_sound_synthesis/max_patches/realworld_sounds/for_testing/Freight_Train-Mono.wav',
                 '/Users/apg250/git/automatic_programming_sound_synthesis/max_patches/realworld_sounds/for_testing/Lion-Growling-Mono.wav',
                 '/Users/apg250/git/automatic_programming_sound_synthesis/max_patches/realworld_sounds/for_testing/RandomAnalogReverb-Ballad-Mono.wav',
                 '/Users/apg250/git/automatic_programming_sound_synthesis/max_patches/realworld_sounds/for_testing/Synth-Metallic-IDM-Pad-Mono.wav']
               
    test1_features = get_features(FILENAMES[0], 'nlse')
    test2_features = get_features(FILENAMES[1], 'nlse')
    print get_similarity(test1_features, test2_features, 'euclidean')
    
if __name__ == '__main__':
    main()