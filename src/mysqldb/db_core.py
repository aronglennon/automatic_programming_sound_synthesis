# This file contains general mysql db operations

import mysql.connector
import platform
if platform.python_implementation()=='CPython':
    import numpy as np
else:
    import numpypy as np
import datetime
from db_config import Config 

def getDBname():
    cfghost = Config.dbinfo().copy()['host']
    cfgdb = Config.dbinfo().copy()['database']
    cfguser = Config.dbinfo().copy()['user']
    return "%s / %s / %s" % (cfghost,cfgdb,cfguser)

def openDB(dbname=[]):
    dbConnection = Config().getdbConnection(dbname)
    return dbConnection

def closeDB(dbConnection):
    dbConnection.close()

'''
returns a multi-row set of results
'''
def select(dbConnection, statement):
    cursor = dbConnection.cursor()
    cursor.execute(statement)    
    warnings = cursor.fetchwarnings()
    if warnings:
        values = []
    else:
        values = cursor.fetchall()
    cursor.close()
    return values    

'''
returns a single integer value or [] if no result
'''
def selectValue(dbConnection, statement):
    values = select(dbConnection,statement)
    if not values:
        return []
    else:
        return int(values[0][0])

''' 
for updates that do not return a value
'''
def update(dbConnection, statement):
    cursor = dbConnection.cursor()
    cursor.execute(statement)    
    warnings = cursor.fetchwarnings()
    if warnings:
        result = False
    else:
        result = True
    cursor.close()
    dbConnection.commit()
    return result

'''
for inserts, returns last id of row updated
'''
def insert(dbConnection, statement):
    cursor = dbConnection.cursor()
    cursor.execute(statement)    
    warnings = cursor.fetchwarnings()
    if warnings:
        rowid = []
    else:
        rowid = cursor.lastrowid
    cursor.close()
    dbConnection.commit()
    return rowid         


'''
utility function to insert row into DB and return new unique ID
expects an insert statement on a table where the primary key is an autoincrement
legacy function that can be tossed (just use insert() above); kept just in case 
we need to do something different than cursor.lastrowid 
'''
def addRow(dbConnection,statement):
    return insert(dbConnection,statement)
    
'''
retrieve database server current time (UTC/GMT)
'''
def getCurrentTimeFromDB(dbConnection):
    values = select(dbConnection,"select now();")
    if values:
        return datetime.datetime.strptime(str(values[0][0]), "%Y-%m-%d %H:%M:%S")
    else:
        return []