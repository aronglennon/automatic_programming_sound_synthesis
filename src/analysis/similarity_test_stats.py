#NOTE: normalizations taken using max/min vals of each measure, since scaling isn't the point here,
# but rather trends with increased distortion

from mysqldb.db_commands import mysql_object
import matplotlib.pyplot as plt
from operator import itemgetter

TESTRUN_ID = 124

def main():
    DTW_Vals = []
    DTW_xs = []
    DPLA_Vals = []
    DPLA_xs = []
    SIC_DPLA_Vals = []
    SIC_DPLA_xs = []
    Euc_Vals = []
    Euc_xs = []    
    # NOTE: Currently, this code just outputs similarity scores sorted by some other column (e.g. total amount deleted in the sampdel tests)
    mysql_obj = mysql_object(sameThread = True)
    table = 'tsts'
    sort_by_column = 'scale_percent'
    #values = mysql_obj.get_similarity_test_data(table, sort_by_column, TESTRUN_ID)
    
    #values = mysql_obj.get_content_intro_similarity_test_data(TESTRUN_ID, 'DTW') 
    #values = mysql_obj.get_repinsert_similarity_test_data(TESTRUN_ID, 'DTW')
    #values = mysql_obj.get_tsts_similarity_test_data(TESTRUN_ID, 'DTW')
    #values = mysql_obj.get_tw_similarity_test_data(TESTRUN_ID, 'DTW')
    values = mysql_obj.get_sampdel_similarity_test_data(TESTRUN_ID, 'DTW')
    #values = mysql_obj.get_stableextension_similarity_test_data(TESTRUN_ID, 'DTW')
    #values = mysql_obj.get_reorder_similarity_test_data(TESTRUN_ID, 'DTW')
    
    sortedVals = sorted(values, key=itemgetter(1))
    for v in sortedVals:
        dtwVal = v[0]
        dtwVal = (dtwVal-0.35148740112781524)/(0.9172393918037415-0.35148740112781524)
        DTW_xs.append(v[1])
        DTW_Vals.append(dtwVal)
    #values = mysql_obj.get_content_intro_similarity_test_data(TESTRUN_ID, 'DPLA') 
    #values = mysql_obj.get_repinsert_similarity_test_data(TESTRUN_ID, 'DPLA')
    #values = mysql_obj.get_tsts_similarity_test_data(TESTRUN_ID, 'DPLA')
    #values = mysql_obj.get_tw_similarity_test_data(TESTRUN_ID, 'DPLA')
    values = mysql_obj.get_sampdel_similarity_test_data(TESTRUN_ID, 'DPLA')
    #values = mysql_obj.get_stableextension_similarity_test_data(TESTRUN_ID, 'DPLA')
    #values = mysql_obj.get_reorder_similarity_test_data(TESTRUN_ID, 'DPLA')

    sortedVals = sorted(values, key=itemgetter(1))
    for v in sortedVals:
        dplaVal = v[0]
        dplaVal = (dplaVal-0.44070619344711304)/(0.9657181859016418-0.44070619344711304)
        DPLA_xs.append(v[1])
        DPLA_Vals.append(dplaVal)
    #values = mysql_obj.get_content_intro_similarity_test_data(TESTRUN_ID, 'SIC-DPLA') 
    #values = mysql_obj.get_repinsert_similarity_test_data(TESTRUN_ID, 'SIC-DPLA')
    #values = mysql_obj.get_tsts_similarity_test_data(TESTRUN_ID, 'SIC-DPLA')
    #values = mysql_obj.get_tw_similarity_test_data(TESTRUN_ID, 'SIC-DPLA')  
    values = mysql_obj.get_sampdel_similarity_test_data(TESTRUN_ID, 'SIC-DPLA')
    #values = mysql_obj.get_stableextension_similarity_test_data(TESTRUN_ID, 'SIC-DPLA')
    #values = mysql_obj.get_reorder_similarity_test_data(TESTRUN_ID, 'SIC-DPLA')
    
    sortedVals = sorted(values, key=itemgetter(1))
    for v in sortedVals:
        sicDplaVal = v[0]
        sicDplaVal = (sicDplaVal-0.45595999658107755)/(0.9804926037788391-0.45595999658107755)
        SIC_DPLA_xs.append(v[1])
        SIC_DPLA_Vals.append(sicDplaVal)
    #values = mysql_obj.get_content_intro_similarity_test_data(TESTRUN_ID, 'euclidean') 
    #values = mysql_obj.get_repinsert_similarity_test_data(TESTRUN_ID, 'euclidean')
    #values = mysql_obj.get_tsts_similarity_test_data(TESTRUN_ID, 'euclidean')
    #values = mysql_obj.get_tw_similarity_test_data(TESTRUN_ID, 'euclidean')
    values = mysql_obj.get_sampdel_similarity_test_data(TESTRUN_ID, 'euclidean')
    #values = mysql_obj.get_stableextension_similarity_test_data(TESTRUN_ID, 'euclidean')
    #values = mysql_obj.get_reorder_similarity_test_data(TESTRUN_ID, 'euclidean')
    
    sortedVals = sorted(values, key=itemgetter(1))
    for v in sortedVals:
        # take away prior incorrect normalization
        eucVal = v[0]
        eucVal = (eucVal-0.8518630027770996)/(0.9814877986907959-0.8518630027770996)
        Euc_xs.append(v[1])
        Euc_Vals.append(eucVal)
    '''
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
            eucVal = 1.0 - v[1]
            eucVal = 1.0 - (4*np.sqrt(2))*eucVal
            Euc_xs.append(v[2])
            Euc_Vals.append(eucVal)
    '''
    font = {'family' : 'normal',
        'weight' : 'bold',
        'size'   : 20}

    matplotlib.rc('font', **font)
    plt.figure(facecolor='white')
    plt.title('Sample Deletion')
    plt.xlabel('Total % Deleted')
    plt.ylabel('Similarity Score')
    plt.plot(DTW_xs, DTW_Vals, '-', hold = True, alpha = 0.8)
    plt.plot(DPLA_xs, DPLA_Vals, '-', hold = True, alpha = 0.8)
    plt.plot(SIC_DPLA_xs, SIC_DPLA_Vals, '-', hold = True, alpha = 0.8)
    plt.plot(Euc_xs, Euc_Vals, '-', hold = True, alpha = 0.8)
    plt.axis(ymin = 0.0, ymax = 1.0)
    plt.axis(xmin = 2, xmax = 75)
    plt.legend(('DTW', 'DPLA', 'SIC-DPLA', 'Euclidean'), loc = 3)
    plt.show()
    
if __name__ == "__main__":
    main()