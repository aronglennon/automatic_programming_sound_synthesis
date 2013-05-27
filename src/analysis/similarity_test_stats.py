from mysqldb.db_commands import mysql_object
import matplotlib.pyplot as plt
from operator import itemgetter


def main():
    # NOTE: Currently, this code just outputs similarity scores sorted by some other column (e.g. total amount deleted in the sampdel tests)
    mysql_obj = mysql_object(sameThread = True)
    table = 'repinsert'
    sort_by_column = 'total_length_reps'
    values = mysql_obj.get_similarity_test_data(table, sort_by_column)
    valsToPlot = []
    sortedVals = sorted(values, key=itemgetter(2))
    for v in sortedVals:
        if v[0] == 'euclidean' and v[2] != 0:
            valsToPlot.append(v[1])
    
    plt.plot(valsToPlot)
    plt.show()
    
if __name__ == "__main__":
    main() 