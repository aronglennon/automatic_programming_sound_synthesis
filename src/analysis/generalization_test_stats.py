from mysqldb.db_commands import mysql_object
import matplotlib.pyplot as plt
from operator import itemgetter

TESTRUN_ID = 19

'''
Parameter Set: TBD once all other tests have been run

The performance of the system is usually measured using the fitness level at which the system converges and how long it takes to converge to that level. 
We have calculated the typical statistics (min, max, mean) over each stopping criteria variation for each individual target as well as all targets combined.
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