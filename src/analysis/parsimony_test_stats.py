from mysqldb.db_commands import mysql_object
import matplotlib.pyplot as plt
from operator import itemgetter
import numpy as np
from scipy.optimize import curve_fit

testruns = [575]#[398, 401, 404, 416, 407]#, 420, 423, 426, 429, 432, 435, 438, 442, 445, 451, 454, 457, 460, 463, 466]
#testruns = [399, 402, 405, 417, 414]#[399, 402, 405, 417, 414]#, 421, 424, 427, 430, 433, 436, 440, 443, 446, 452, 458, 461, 464, 467]
#testruns = [400, 403, 406, 419, 415]#, 422, 425, 428, 431, 434, 437, 441, 444, 449, 453, 456, 459, 462, 465, 468]

# curve fitting function
def expfunc(x, a, b, c):
    return a*np.exp(-b*x)+c

def linfunc(x, a, b):
    return a*x + b

'''
Parameter Sets: 8-13

200 iterations of 100 individuals

On each permutation of the aforementioned limitation, we are interested in recording the fitness of the best-of-run individual, 
the iteration/generation in which that individual was created, the total number of iterations in each run, 
and the trends of average fitness of each generation, maximum fitness in each generation, and minimum fitness in each generation
'''
def main():
    font = {'family' : 'normal',
        'weight' : 'bold',
        'size'   : 20}

    matplotlib.rc('font', **font)
    plt.figure(facecolor='white')
    # NOTE: Currently, this code just outputs similarity scores sorted by some other column (e.g. total amount deleted in the sampdel tests)
    mysql_obj = mysql_object(sameThread = True)
    # input testrun, get back (best of run fitness, generation, patch, count)
    plotNum = 1    
    for t in testruns:    
        best_of_run = mysql_obj.get_best_of_run(t)
        print 'best fitness: %0.8f' % best_of_run[0][0]
        total_iterations = mysql_obj.get_total_num_iterations(t)
        avg_fitness = np.array(mysql_obj.get_avg_fitness_per_generation(t))
        max_fitness = np.array(mysql_obj.get_max_fitness_per_generation(t))
        min_fitness = np.array(mysql_obj.get_min_fitness_per_generation(t))
        
        #plt.axis(xmin = 0.0, xmax = 200.0, ymin = 0.7, ymax = 1.0, hold = True)
        # Plot min, avg, max fitness over generations
        #plt.plot(range(0,200), min_fitness, linewidth=2, color='r', hold = True)
        generations = np.arange(0, len(max_fitness), dtype=np.float)
        '''
        expParam, pcov = curve_fit(expfunc, generations, avg_fitness ) 
        linParam, pcov = curve_fit(linfunc, generations, avg_fitness )
        print 'exp for avg'    
        print '%0.8f * exp(-%0.8f * x) + %0.8f' % (expParam[0], expParam[1], expParam[2])
        print 'lin for avg'
        print '%0.8f * x + %0.8f' % (linParam[0], linParam[1])
        trialX = np.linspace(generations[0],generations[-1],1000)    
        yExp = expfunc(trialX, *expParam)
        yLin = linfunc(trialX, *linParam)
        plt.plot(generations, avg_fitness, linewidth=2, color='g', hold = True)    
        plt.plot(trialX, yExp, 'r-',ls='--', label="Exp Fit Avg", hold = True)
        plt.plot(trialX, yLin, 'b-',ls='--', label="Lin Fit Avg", hold = True)    
        '''
        #expParam, pcov = curve_fit(expfunc, generations, max_fitness )  
        #linParam, pcov = curve_fit(linfunc, generations, max_fitness )
        print 'exp for max'    
        #print '%0.8f * exp(-%0.8f * x) + %0.8f' % (expParam[0], expParam[1], expParam[2])
        #print 'lin for max'
        #print '%0.8f * x + %0.8f' % (linParam[0], linParam[1])
        trialX = np.linspace(generations[0],generations[-1],1000)    
        #yExp = expfunc(trialX, *expParam)
        #yLin = linfunc(trialX, *linParam)
        plt.plot(generations, avg_fitness, '-',ls='--', linewidth = 1, label="%d" % t, hold = True)    
        #plt.plot(trialX, yExp, '-',ls='--', linewidth = (plotNum / 5)+1, label="%d" % t, hold = True)    
        #plt.plot(trialX, yLin, 'g-',ls='--', label="Lin Fit Max", hold = True)     
        plotNum += 1
    plt.title('Parsimony')
    plt.xlabel('Generation')
    plt.ylabel('Fitness')
    plt.legend(('SMTD - 6', 'SMTD - 8', 'SMTD - 10', 'SMTD - 12', 'SMTD - 14'), loc=4)
    plt.show()
    
if __name__ == "__main__":
    main()