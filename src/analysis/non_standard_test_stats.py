from mysqldb.db_commands import mysql_object
import matplotlib.pyplot as plt
from operator import itemgetter

TESTRUN_ID = 19

'''
Parameter Sets: 26-28

We calculate statistics on how quickly (i.e. how few iterations) we are able to perform in order to find a near optimal solution. 
In the case of using SA in combination with GP, it is not immediately clear how to directly compare this strategy with standard GP, 
due to the internal iterations SA proceeds through within each GP iteration. In this case, the number of algorithms searched 
(i.e. translated into the Max environment for audio processing) will be used for a fair comparison.
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