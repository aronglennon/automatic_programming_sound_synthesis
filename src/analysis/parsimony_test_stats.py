from mysqldb.db_commands import mysql_object
import matplotlib.pyplot as plt
from operator import itemgetter

TESTRUN_ID = 210

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
    best_of_run = mysql_obj.get_best_of_run(TESTRUN_ID)
    print best_of_run
    total_iterations = mysql_obj.get_total_num_iterations(TESTRUN_ID)
    print total_iterations
    avg_fitness = mysql_obj.get_avg_fitness_per_generation(TESTRUN_ID)
    print avg_fitness
    max_fitness = mysql_obj.get_max_fitness_per_generation(TESTRUN_ID)
    print max_fitness
    min_fitness = mysql_obj.get_min_fitness_per_generation(TESTRUN_ID)
    print min_fitness
    plt.figure(facecolor='white')
    plt.axis(xmin = 0.0, xmax = 200.0, ymin = 0.8, ymax = 1.0, hold = True)
    # Plot min, avg, max fitness over generations
    #plt.plot(range(0,200), min_fitness, linewidth=2, color='r', hold = True)
    plt.plot(range(0,200), avg_fitness, linewidth=2, color='g', hold = True)
    plt.plot(range(0,200), max_fitness, linewidth=2, color='b', hold = True)
    plt.title('Parsimony')
    plt.xlabel('Generation')
    plt.ylabel('Fitness')
    plt.show()
    
if __name__ == "__main__":
    main()