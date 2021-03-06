# This file contains the mysql_object class with appropriate commands

import threading
import mysql.connector
from mysql.connector.errors import OperationalError
import platform
import numpy as np
import datetime, time
from datetime import timedelta
from mysqldb.db_config import Config
from mysql.connector.errors import InterfaceError
from mysqldb import db_core
import sys
import string
            
class mysql_connection_thread (threading.Thread):
    def __init__ (self, mysql_object):
        self.mysql_object = mysql_object
        threading.Thread.__init__ (self)
        self.daemon = True
        self.name = "mysql_connection_thread"
        
    def run(self):
        count = 1
        while count <= 64:
            try:
                # create connection to host and post given
                self.mysql_object.dbConnection = mysql.connector.connect(**(self.mysql_object.config))
                db_core.update(self.epgObject.dbConnection,"SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED")
                # access test database instance
                self.mysql_object.connected = True
                break
            except:
                time.sleep(count)
                count *= 2
        while self.mysql_object.connected == False:
            try:
                # create connection to host and post given
                self.mysql_object.dbConnection = mysql.connector.connect(**self.mysql_object.config)
                db_core.update(self.mysql_object.dbConnection,"SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED")
                # access test database instance
                self.mysql_object.connected = True
                break
            except:
                time.sleep(count)

class mysql_object():
    def __init__(self, dbName='localhost', backoff=True, sameThread = False):
        self.config = Config().dbinfo(dbName)
        self.backoff = backoff
        self.sameThread = sameThread
        self.dbConnection = []
        self.connected = False
        self.connectionThread = mysql_connection_thread(self)
        self.connect()
        
    def __del__(self):
        if (self.dbConnection.connection_id is not None):
            self.dbConnection.close()
            self.connected = False
        
    def connect(self):
        if self.backoff == True:
            if self.sameThread == False:
                if (not self.connectionThread.isAlive()):
                    # this is only run if a connection thread is not alive, so on init of mysql_object, a second connection thread is not created, even though it might look like it.
                    self.connectionThread = mysql_connection_thread(self)
                    self.connectionThread.start()
            else:
                    count = 1
                    while count <= 64:
                        try:
                            # create connection to host and post given
                            self.dbConnection = mysql.connector.connect(**self.config)
                            db_core.update(self.dbConnection,"SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED")
                            # access test database instance
                            self.connected = True
                            break
                        except:
                            time.sleep(count)
                            count *= 2
                    while self.connected == False:
                        try:
                            # create connection to host and post given
                            self.dbConnection = mysql.connector.connect(**self.config)
                            db_core.update(self.dbConnection,"SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED")
                            # access test database instance
                            self.connected = True
                            break
                        except:
                            time.sleep(count)
        else:
            try:
                # create connection to host and post given
                self.dbConnection = mysql.connector.connect(**self.config)
                db_core.update(self.dbConnection,"SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED")
                # access test database instance
                self.connected = True
                return True
            except:
                self.connected = False
                    
    def query(self, statement):
        try:
            values = db_core.select(self.dbConnection,statement)
        except Exception, e:
            self.__del__()
            self.connect()
            if self.connected:
                try:
                    values = db_core.select(self.dbConnection,statement)
                except:
                    self.__del__()
                    return []
        return values
    
    '''
    look up a parameter set based on ID
    '''
    def lookup_parameter_set(self,parameter_id):
        if self.connected:
            statement = "SELECT * FROM parameters WHERE parameter_set_id = %d" % parameter_id
            values = self.query(statement)
            return values
        else:
            return []
        
    def new_test_run(self, time):
        if self.connected:
            statement = "INSERT INTO testrun (start_time) VALUES ('%s')" % time
            values = db_core.insert(self.dbConnection, statement)
            return values
        else:
            return []
        
    def close_test_run(self, testrun_id, run_end):
        if self.connected:
            statement = "UPDATE testrun SET end_time = '%s' WHERE testrun_id = %s" % (run_end, testrun_id)
            values = db_core.update(self.dbConnection, statement)
            return values
        else:
            return []
        
    def insert_full_test_data(self, testrun_id, generation_number, individual, fitness, count, subgroup, parameter_set, max_tree_depth, resource_count, patch_type, exchange_frequency, exchange_proportion, simulated_annealing_size, obj_list_file, target_file):
        if self.connected:
            statement = "INSERT INTO testdata (testrun_id, generation, individual, fitness, count, subgroup, parameter_set, max_tree_depth, resource_count, patch_type, exchange_frequency, exchange_proportion, simulated_annealing_size, obj_list_file, target_file) \
            VALUES (%d, %d, '%s', %0.8f, %d, %d, %d, %d, %d, '%s', %d, %0.8f, %d, '%s', '%s')" % (testrun_id, generation_number, individual, fitness, count, subgroup, parameter_set, max_tree_depth, resource_count, patch_type, exchange_frequency, exchange_proportion, simulated_annealing_size, obj_list_file, target_file)
            values = db_core.insert(self.dbConnection, statement)
            return values
        else:
            return []
        
    def insert_tsts_test_data(self, test_run_id, test_case, filename, scale_percent, shift_amount, sim_type, sim_val):
        if self.connected:
            statement = "INSERT INTO testdata_similarity_tsts (testrun_id, testcase_id, filename, scale_percent, shift_amount, sim_type, sim_val) \
            VALUES (%d, %d, '%s', %0.8f, %0.8f, '%s', %0.8f)" % (test_run_id, test_case, filename, scale_percent, shift_amount, sim_type, sim_val)
            values = db_core.insert(self.dbConnection, statement)
            return values
        else:
            return []

    def insert_tw_test_data(self, test_run, test_case, filename, min_warping_threshold, max_warping_threshold, warping_path, sim_type, sim_val):
        if self.connected:
            if min_warping_threshold is None:
                min_warping_threshold = 0
            elif max_warping_threshold is None:
                max_warping_threshold = 0
            statement = "INSERT INTO testdata_similarity_tw (testrun_id, testcase_id, filename, min_warping_threshold, max_warping_threshold, warping_path, sim_type, sim_val) \
            VALUES (%d, %d, '%s', %d, %d, '%s', '%s', %0.8f)" % (test_run, test_case, filename, min_warping_threshold, max_warping_threshold, warping_path, sim_type, sim_val)
            values = db_core.insert(self.dbConnection, statement)
            return values
        else:
            return []

    def insert_sampdel_test_data(self, test_run, test_case, filename, total_deleted_content, num_segments, max_segment, min_segment, avg_segment, sim_type, sim_val):
        if self.connected:
            statement = "INSERT INTO testdata_similarity_sampdel (testrun_id, testcase_id, filename, num_segments, max_segment_length, min_segment_length, average_segment_length, total_deleted_content, sim_type, sim_val) \
            VALUES (%d, %d, '%s', %d, %d, %d, %0.8f, %0.8f, '%s', %0.8f)" % (test_run, test_case, filename, num_segments, max_segment, min_segment, avg_segment, total_deleted_content, sim_type, sim_val)
            values = db_core.insert(self.dbConnection, statement)
            return values
        else:
            return []
    
    def insert_stableextension_test_data(self, test_run, test_case, filename, total_content_extended, num_segments, max_segment, min_segment, avg_segment, sim_type, sim_val):
        if self.connected:
            statement = "INSERT INTO testdata_similarity_stableextension (testrun_id, testcase_id, filename, total_content_extended, num_segments, max_segment, min_segment, avg_segment, sim_type, sim_val) \
            VALUES (%d, %d, '%s', %0.8f, %d, %d, %d, %0.8f, '%s', %0.8f)" % (test_run, test_case, filename, total_content_extended, num_segments, max_segment, min_segment, avg_segment, sim_type, sim_val)
            values = db_core.insert(self.dbConnection, statement)
            return values
        else:
            return []

    def insert_contentintro_test_data(self, test_run, test_case, filename, total_percent_introduction, total_percent_deletion, file_introduced, num_introduction, max_introduction, min_introduction, avg_introduction, num_deletion, max_deletion, min_deletion, avg_deletion, sim_type, sim_val):
        if self.connected:
            statement = "INSERT INTO testdata_similarity_contentintro (testrun_id, testcase_id, filename, intro_filename, total_percent_introduction, total_percent_deletion, num_intro, max_intro, min_intro, avg_intro, num_delete, max_delete, min_delete, avg_delete, sim_type, sim_val) \
            VALUES (%d, %d, '%s', '%s', %0.8f, %0.8f, %d, %d, %d, %0.8f, %d, %d, %d, %0.8f, '%s', %0.8f)" % (test_run, test_case, filename, file_introduced, total_percent_introduction, total_percent_deletion, num_introduction, max_introduction, min_introduction, avg_introduction, num_deletion, max_deletion, min_deletion, avg_deletion, sim_type, sim_val)
            values = db_core.insert(self.dbConnection, statement)
            return values
        else:
            return []

    def insert_reorder_test_data(self, test_run, test_case, filename, num_swaps, max_size, min_size, total_size, avg_size, sim_type, sim_val):
        if self.connected:
            statement = "INSERT INTO testdata_similarity_reorder (testrun_id, testcase_id, filename, num_swaps, max_size, min_size, total_size, avg_size, sim_type, sim_val) \
            VALUES (%d, %d, '%s', %d, %d, %d, %d, %0.8f, '%s', %0.8f)" % (test_run, test_case, filename, num_swaps, max_size, min_size, total_size, avg_size, sim_type, sim_val)
            values = db_core.insert(self.dbConnection, statement)
            return values
        else:
            return []
        
    def insert_repinsert_test_data(self, test_run, test_case, filename, num_reps, num_unique_reps, max_reps_for_unique, min_reps_for_unique, avg_reps, total_length_reps, total_length_deletes, num_segment_deletes, max_delete, min_delete, max_rep_length, min_rep_lenth, avg_rep_length, avg_delete_length, sim_type, sim_val):
        if self.connected:
            statement = "INSERT INTO testdata_similarity_repinsert (testrun_id, testcase_id, filename, num_unique_reps, max_reps_for_unique, min_reps_for_unique, total_reps, avg_reps, total_length_reps, total_length_deletes, num_seg_deletes, max_del, min_del, max_rep, min_rep, avg_rep, avg_del, sim_type, sim_val) \
            VALUES (%d, %d, '%s', %d, %d, %d, %d, %0.8f, %d, %d, %d, %d, %d, %d, %d, %0.8f, %0.8f, '%s', %0.8f)" % (test_run, test_case, filename, num_unique_reps, max_reps_for_unique, min_reps_for_unique, num_reps, avg_reps, total_length_reps, total_length_deletes, num_segment_deletes, max_delete, min_delete, max_rep_length, min_rep_lenth, avg_rep_length, avg_delete_length, sim_type, sim_val)
            values = db_core.insert(self.dbConnection, statement)
            return values
        else:
            return []
        
    def insert_genops_test_data(self, test_run, test_case, target_filename, patch, patch_fitness, neighbor, neighbor_fitness, max_tree_depth, patch_type, tournament_size, obj_list_file):
        if self.connected:
            statement = "INSERT INTO testdata_genops (testrun_id, testcase_id, target_file, patch, patch_fitness, neighbor, neighbor_fitness, max_tree_depth, patch_type, tournament_size, obj_list_file) \
            VALUES (%d, %d, '%s', '%s', %0.8f, '%s', %0.8f, %d, '%s', %d, '%s')" % (test_run, test_case, target_filename, patch, patch_fitness, neighbor, neighbor_fitness, max_tree_depth, patch_type, tournament_size, obj_list_file)
            values = db_core.insert(self.dbConnection, statement)
            return values
        else:
            return []
        
    def get_similarity_test_data(self, table_name, sort_by, testrun):
        if self.connected:
            statement = "SELECT sim_type, sim_val, %s FROM testdata_similarity_%s WHERE testrun_id = %d" % (sort_by, table_name, testrun)
            values = db_core.select(self.dbConnection, statement)
            return values
        else:
            return []
    
    def get_repinsert_similarity_test_data(self, testrun, sim_type):
        if self.connected:
            statement = "SELECT avg(sim_val), avg(total_length_reps)/44100 FROM testdata_similarity_repinsert WHERE testrun_id = %d AND sim_type = \"%s\" group by testcase_id" % (testrun, sim_type)
            values = db_core.select(self.dbConnection, statement)
            return values
        else:
            return []  
            
    def get_tsts_similarity_test_data(self, testrun, sim_type):
        if self.connected:
            statement = "SELECT avg(sim_val), scale_percent FROM automatic_programming_sound_synthesis.testdata_similarity_tsts WHERE testrun_id = %d AND sim_type = \"%s\" group by scale_percent;" % (testrun, sim_type)
            values = db_core.select(self.dbConnection, statement)
            return values
        else:
            return [] 

    def get_sampdel_similarity_test_data(self, testrun, sim_type):
        if self.connected:
            statement = "SELECT avg(sim_val), total_deleted_content FROM automatic_programming_sound_synthesis.testdata_similarity_sampdel WHERE testrun_id = %d AND sim_type = \"%s\" group by testcase_id;" % (testrun, sim_type)
            values = db_core.select(self.dbConnection, statement)
            return values
        else:
            return [] 

    def get_stableextension_similarity_test_data(self, testrun, sim_type):
        if self.connected:
            statement = "SELECT avg(sim_val), total_content_extended FROM automatic_programming_sound_synthesis.testdata_similarity_stableextension WHERE testrun_id = %d AND sim_type = \"%s\" group by testcase_id;" % (testrun, sim_type)
            values = db_core.select(self.dbConnection, statement)
            return values
        else:
            return []
    
    def get_reorder_similarity_test_data(self, testrun, sim_type):
        if self.connected:
            statement = "SELECT avg(sim_val), total_size/44100 FROM automatic_programming_sound_synthesis.testdata_similarity_reorder WHERE testrun_id = %d AND sim_type = \"%s\" GROUP BY testcase_id;" % (testrun, sim_type)
            values = db_core.select(self.dbConnection, statement)
            return values
        else:
            return []    

    def get_tw_similarity_test_data(self, testrun, sim_type):
        if self.connected:
            statement = "SELECT avg(sim_val), max_warping_threshold FROM automatic_programming_sound_synthesis.testdata_similarity_tw WHERE testrun_id = %d AND sim_type = \"%s\" AND min_warping_threshold = 0 group by max_warping_threshold" % (testrun, sim_type)
            values = db_core.select(self.dbConnection, statement)
            return values
        else:
            return [] 
    
    def get_content_intro_similarity_test_data(self, testrun, sim_type):
        if self.connected:
            statement = "SELECT avg(sim_val), total_percent_introduction FROM testdata_similarity_contentintro WHERE testrun_id = %d AND sim_type = \"%s\" group by total_percent_deletion" % (testrun, sim_type)
            values = db_core.select(self.dbConnection, statement)
            return values
        else:
            return []    
    
    def get_genops_test_data(self, testrun, bad_vals):
        if self.connected:
            statement = "SELECT patch_fitness, max(neighbor_fitness) FROM automatic_programming_sound_synthesis.testdata_genops WHERE testrun_id IN (%s) AND patch_fitness != neighbor_fitness AND patch_fitness NOT IN (%s) AND neighbor_fitness NOT IN (%s) GROUP BY testcase_id;" % (','.join([str(s) for s in testrun]), ','.join([str(b) for b in bad_vals]), ','.join([str(b) for b in bad_vals]))
            values = db_core.select(self.dbConnection, statement)
            return values
        else:
            return []
        
    def get_best_of_run(self, testrun):
        if self.connected:
            statement = "SELECT fitness, generation, individual, count FROM testdata WHERE testrun_id = %d ORDER BY fitness DESC LIMIT 20;" % (testrun)
            values = db_core.select(self.dbConnection, statement)
            return values
        else:
            return []
        
    def get_total_num_iterations(self, testrun):
        if self.connected:
            statement = "SELECT COUNT(*) FROM testdata WHERE testrun_id = %d" % (testrun)
            values = db_core.select(self.dbConnection, statement)
            return values
        else:
            return []
        

    def get_avg_fitness_per_generation(self, testrun):
        if self.connected:
            statement = "SELECT AVG(fitness) FROM testdata WHERE testrun_id = %d GROUP BY generation" % (testrun)
            values = db_core.select(self.dbConnection, statement)
            return [float(x) for x in [y[0] for y in values]]
        else:
            return []
        
    def get_max_fitness_per_generation(self, testrun):
        if self.connected:
            statement = "SELECT MAX(fitness) FROM testdata WHERE testrun_id = %d GROUP BY generation" % (testrun)
            values = db_core.select(self.dbConnection, statement)
            return [float(x) for x in [y[0] for y in values]]
        else:
            return []
        
    def get_min_fitness_per_generation(self, testrun):
        if self.connected:
            statement = "SELECT MIN(fitness) FROM testdata WHERE testrun_id = %d GROUP BY generation" % (testrun)
            values = db_core.select(self.dbConnection, statement)
            return [float(x) for x in [y[0] for y in values]]
        else:
            return []
    def get_last_generation(self, testrun_id):
        if self.connected:
            statement = "SELECT generation, individual, fitness FROM testdata WHERE generation = (SELECT max(generation) FROM testdata where testrun_id = %d) and testrun_id = %d;" % (testrun_id, testrun_id)
            values = db_core.select(self.dbConnection, statement)
            return values
        else:
            return []
        
def main():
    usage = "usage: %prog"
    
    mysql_obj = mysql_object()
    params = mysql_obj.lookup_parameter_set(0)
    print params

if __name__ == '__main__':
    main()
