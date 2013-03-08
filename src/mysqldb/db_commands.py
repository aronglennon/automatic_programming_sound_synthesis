# This file contains the mysql_object class with appropriate commands

import threading
import mysql.connector
from mysql.connector.errors import OperationalError
import platform
if platform.python_implementation()=='CPython':
    import numpy as np
else:
    import numpypy as np
import datetime, time
from datetime import timedelta
from config import Config
from mysql.connector.errors import InterfaceError
import general_db
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
                self.mysql_object.dbConnection = mysql.connector.Connect(**(self.mysql_object.config))
                general_db.update(self.epgObject.dbConnection,"SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED")
                # access test database instance
                self.mysql_object.connected = True
                break
            except:
                time.sleep(count)
                count *= 2
        while self.mysql_object.connected == False:
            try:
                # create connection to host and post given
                self.mysql_object.dbConnection = mysql.connector.Connect(**self.mysql_object.config)
                general_db.update(self.mysql_object.dbConnection,"SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED")
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
                            self.dbConnection = mysql.connector.Connect(**self.config)
                            general_db.update(self.dbConnection,"SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED")
                            # access test database instance
                            self.connected = True
                            break
                        except:
                            time.sleep(count)
                            count *= 2
                    while self.connected == False:
                        try:
                            # create connection to host and post given
                            self.dbConnection = mysql.connector.Connect(**self.config)
                            general_db.update(self.dbConnection,"SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED")
                            # access test database instance
                            self.connected = True
                            break
                        except:
                            time.sleep(count)
        else:
            try:
                # create connection to host and post given
                self.dbConnection = mysql.connector.Connect(**self.config)
                general_db.update(self.dbConnection,"SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED")
                # access test database instance
                self.connected = True
                return True
            except:
                self.connected = False
                    
    def query(self, statement):
        try:
            values = general_db.select(self.dbConnection,statement)
        except Exception, e:
            self.__del__()
            self.connect()
            if self.connected:
                try:
                    values = general_db.select(self.dbConnection,statement)
                except:
                    self.__del__()
                    return []
        return values
    
    '''
    look up a parameter set based on ID
    '''
    def lookup_parameter_set(self,parameter_id):
        if self.connected:
            statement = "SELECT * FROM parameter WHERE id = %d" % parameter_id
            values = self.query(statement)
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
