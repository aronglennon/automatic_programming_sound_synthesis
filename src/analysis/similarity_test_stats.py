from mysqldb.db_commands import mysql_object
import matplotlib.pyplot as plt
from operator import itemgetter

TESTRUN_ID = 19

def main():
    # NOTE: Currently, this code just outputs similarity scores sorted by some other column (e.g. total amount deleted in the sampdel tests)
    mysql_obj = mysql_object(sameThread = True)
    table = 'repinsert'
    sort_by_column = 'total_length_reps'
    values = mysql_obj.get_similarity_test_data(table, sort_by_column, TESTRUN_ID)
    DTW_Vals = []
    DPLA_Vals = []
    SIC_DPLA_Vals = []
    Euc_Vals = []
    sortedVals = sorted(values, key=itemgetter(2))
    for v in sortedVals:
        if v[0] == 'DTW' and v[2] != 0:
            DTW_Vals.append(1.0-5.0*(1.0-v[1]))
        elif v[0] == 'DPLA' and v[2] != 0:
            DPLA_Vals.append(1.0-5.0*(1.0-v[1]))
        elif v[0] == 'SIC-DPLA' and v[2] != 0:
            SIC_DPLA_Vals.append(1.0-5.0*(1.0-v[1]))
        elif v[0] == 'euclidean' and v[2] != 0:
            Euc_Vals.append(1.0-5.0*(1.0-v[1]))
    plt.plot(DTW_Vals, hold = True)
    plt.plot(DPLA_Vals, hold = True)
    plt.plot(SIC_DPLA_Vals, hold = True)
    plt.plot(Euc_Vals, hold = True)
    plt.axis(ymin = 0.0, ymax = 1.0)
    plt.legend('asdf')
    plt.show()
    
if __name__ == "__main__":
    main()