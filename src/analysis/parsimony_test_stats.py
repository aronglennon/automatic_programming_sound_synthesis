from mysqldb.db_commands import mysql_object
import matplotlib.pyplot as plt
from operator import itemgetter

TESTRUN_ID = 19

'''
Parameter Sets: 8-13

200 iterations of 100 individuals

On each permutation of the aforementioned limitation, we are interested in recording the fitness of the best-of-run individual, 
the iteration/generation in which that individual was created, the total number of iterations in each run, 
and the trends of average fitness of each generation, maximum fitness in each generation, and minimum fitness in each generation
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