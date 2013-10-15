from mysqldb.db_commands import mysql_object
import matplotlib.pyplot as plt
from operator import itemgetter

TESTRUN_ID = 124

def main():
    # NOTE: Currently, this code just outputs similarity scores sorted by some other column (e.g. total amount deleted in the sampdel tests)
    mysql_obj = mysql_object(sameThread = True)
    table = 'contentintro'
    sort_by_column = 'total_percent_deletion'
    values = mysql_obj.get_similarity_test_data(table, sort_by_column, TESTRUN_ID)
    DTW_Vals = []
    DTW_xs = []
    DPLA_Vals = []
    DPLA_xs = []
    SIC_DPLA_Vals = []
    SIC_DPLA_xs = []
    Euc_Vals = []
    Euc_xs = []
    sortedVals = sorted(values, key=itemgetter(2))
    for v in sortedVals:
        if v[0] == 'DTW' and v[2] != 0:
            DTW_xs.append(v[2])
            DTW_Vals.append(v[1])
        elif v[0] == 'DPLA' and v[2] != 0:
            DPLA_xs.append(v[2])
            DPLA_Vals.append(v[1])
        elif v[0] == 'SIC-DPLA' and v[2] != 0:
            SIC_DPLA_xs.append(v[2])
            SIC_DPLA_Vals.append(v[1])
        elif v[0] == 'euclidean' and v[2] != 0:
            Euc_xs.append(v[2])
            Euc_Vals.append(v[1])
    plt.title('Content Introduction')
    plt.xlabel('Total % Deletion')
    plt.ylabel('Similarity')
    plt.plot(DTW_xs, DTW_Vals, '.', hold = True)
    plt.plot(DPLA_xs, DPLA_Vals, '.', hold = True)
    plt.plot(SIC_DPLA_xs, SIC_DPLA_Vals, '.', hold = True)
    plt.plot(Euc_xs, Euc_Vals, '.', hold = True)
    plt.axis(ymin = 0.0, ymax = 1.0)
    plt.legend(('DTW', 'DPLA', 'SIC-DPLA', 'Euclidean'))
    plt.show()
    
if __name__ == "__main__":
    main()