from mysqldb.db_commands import mysql_object
import matplotlib.pyplot as plt
from operator import itemgetter

TESTRUN_ID = 19

'''
Parameter Set: TBD once all other tests are run

The important data we gather from tests include how the best-or-run patches’ fitnesses decrease as we change the cardinality 
of the function set away from only containing necessary functions and as we change the possible parameter values that functions may take, 
as well as recording how the iteration count required to reach a best-of-run patch varies given changes in these variables.
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