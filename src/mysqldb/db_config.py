# -*- coding: utf-8 -*-
# This file contains configuration information for common mysql instances

import mysql.connector

DEFAULT_DATABASE = 'localhost'

class Config():   
    def __init__(self):
        self.dblist = 
        {
         'localhost' : 
                {
                'host'                  : 'localhost',
                'database'              : 'automatic_programming_sound_synthesis',
                'user'                  : 'aronglennon',
                'password'              : 'glennon',
                'port'                  : 3306,
                'charset'               : 'utf8',
                'use_unicode'           : True,
                'get_warnings'          : True,
                'connection_timeout'    : 600
                }
          }
    '''
    fetch info about the db
    '''
    def dbinfo(self,dbname=DEFAULT_DATABASE):
        if not dbname:
            dbname = DEFAULT_DATABASE
        if dbname in self.dblist:
            return self.dblist[dbname]
        else:
            print "Invalid database %s specified!!!" % (dbname)
            return []
    '''
    return an open a connection to a db
    '''        
    def getdbConnection(self,dbname=DEFAULT_DATABASE):
        config = self.dbinfo(dbname)
        dbConnection = mysql.connector.Connect(**config)
        return dbConnection
