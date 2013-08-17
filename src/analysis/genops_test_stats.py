from mysqldb.db_commands import mysql_object
import matplotlib.pyplot as plt
from operator import itemgetter

PARTITION_COUNT = 10
TESTRUN_ID = 46

FITNESS_OFFSET = 0.909448

def main():
    # NOTE: Currently, this code just outputs similarity scores sorted by some other column (e.g. total amount deleted in the sampdel tests)
    mysql_obj = mysql_object(sameThread = True)
    # input testrun, get back (fitness, neighbor fitness)
    values = mysql_obj.get_genops_test_data(TESTRUN_ID, FITNESS_OFFSET)
    # sort on fitness (x-coord in NSC calc)
    sortedVals = sorted(values, key=itemgetter(0))
    maxFitness = sortedVals[-1][0]
    minFitness = sortedVals[0][0]
    original_average_fitnesses = [0] * PARTITION_COUNT
    neighbor_average_fitnesses = [0] * PARTITION_COUNT
    count_fitnesses = [0] * PARTITION_COUNT
    # place counts of all patches in each partition inside count_fitnesses and cumulative sums inside the other two arrays
    for s in sortedVals:
        bucket = int(((s[0]-minFitness) / (maxFitness-minFitness)) * PARTITION_COUNT)
        # fot max fitness exactly
        if bucket == PARTITION_COUNT:
            bucket -= 1
        count_fitnesses[bucket] += 1
        original_average_fitnesses[bucket] += s[0]
        neighbor_average_fitnesses[bucket] += s[1]
    # calculate the actual averages for each partition
    for i in range(0, PARTITION_COUNT):
        original_average_fitnesses[i] /= count_fitnesses[i]
        neighbor_average_fitnesses[i] /= count_fitnesses[i]
    # calculate NSC
    NSC = 0.0
    for i in range(1, PARTITION_COUNT):
        P = (neighbor_average_fitnesses[i] - neighbor_average_fitnesses[i-1]) / (original_average_fitnesses[i] - original_average_fitnesses[i-1])
        if P < 0.0:
            NSC += P
    print 'NSC for testrun %d is %0.8f' % (TESTRUN_ID,NSC)
    
if __name__ == "__main__":
    main()