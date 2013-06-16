from mysqldb.db_commands import mysql_object
import matplotlib.pyplot as plt
from operator import itemgetter

TESTRUN_ID = 19

'''
Parameter Sets: 14-25

200 iterations of 100 individuals

We are interested in determining how the best-of-run average fitness error over all contrived targets varies as we test these combinations 
as well as how they affect the resultant algorithm complexity (measured as the size of the topology of the best-of-run patch). 
Therefore, for each tested combination of initialization mechanism and selection mechanism, we record these values and compare.
'''

def main():
    # NOTE: Currently, this code just outputs similarity scores sorted by some other column (e.g. total amount deleted in the sampdel tests)
    mysql_obj = mysql_object(sameThread = True)
    # input testrun, get back (best of run fitness, generation, patch, count)
    values = mysql_obj.get_best_of_run(TESTRUN_ID)
    print values
    values = mysql_obj.get_total_num_iterations(TESTRUN_ID)
    print values
    values = mysql_obj.get_avg_fitness_per_generation(TESTRUN_ID)
    print values
    values = mysql_obj.get_max_fitness_per_generation(TESTRUN_ID)
    print values
    values = mysql_obj.get_min_fitness_per_generation(TESTRUN_ID)
    print values