def normalizeFitness(patches,minimum,maximum):
    if min(patches) < minimum:
        minimum = min(patches)
    if max(patches) > maximum:
        maximum = max(patches)
    fitnessRange = maximum-minimum
    for p in patches:
        p = (p - min) / fitnessRange
    return patches, minimum, maximum

def change_fitness_to_probability(patches, scaling_type, lowOrHigh):
    print 'change all fitnesses in patches to a probabilty based on whether low fitness is good or not'
    if scaling_type == 'proportionate':
        raw_fitness_sum = 0
        for p in patches:
            raw_fitness_sum += p.fitness
        # scale total fitness to 1
        for p in patches:
            p.fitness /= raw_fitness_sum
        # if low is better, subtract all probs from 1 (which will sum to (num_of_patches - 1)) and then divide by (num_of_patches - 1)
        if lowOrHigh == 'low':
            for p in patches:
                p.fitness = (1-p.fitness)/(len(patches)-1)
    elif scaling_type == 'ranking':
        sum_ranks = (len(patches)+1)*(float(len(patches))/2)
        for i in range (0, len(patches)):
            if lowOrHigh == 'high':
                patches[i].fitness = (len(patches)-i)/sum_ranks
            else:
                patches[i].fitness = i+1/sum_ranks