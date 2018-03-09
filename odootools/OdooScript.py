# -*- coding: utf-8 -*-

'''
Created on march 2018

Utility functions to convert data


@author: C. Guychard
@copyright: ©2018 Article714
@license: AGPL
'''

import datetime
import getopt
import logging
import os.path
import sys

from configobj import ConfigObj

from . import OdooConnection


try:
    import odoo
except:
    odoo = False
    logging.error("error on Odoo import")

try:
    from odoo.tools import config
except:
    config = False

#************************************************
#  CONSTANTS


FORMAT_CONSOLE = '%(levelname)s - %(message)s'
FORMAT_FIC = '%(asctime)s - %(levelname)s - %(message)s'

#************************************************
# Odoo Script
class Script(object):
    '''
    A generic Class to capitalize technical stuffs
    '''
    config = None  
    
    # *************************************************************
    # Constructor, passing arguments from the command line

    def __init__(self, parseConfig=True):
        '''
        Constructor that uses command line arguments to build a config object
        '''
        
        if len (sys.argv) > 1:  
            self.name = os.path.basename(sys.argv[0]).replace('.py', '')
        else:
            self.name = 'Generic OdooScript script'

        #******
        # Basic Logging configuration

        logging.basicConfig(level=logging.INFO, format='%(relativeCreated)6d %(threadName)s %(message)s')

        # Logging configuration
        self.logger = logging.getLogger(self.name)

        #******
        # args parsing
        
        self.configfile = None
        try:
            opts, odooargs = getopt.getopt(sys.argv[1:], "hc:", ["config="])
        except getopt.GetoptError:
            print ('USAGE : \n\t %s.py -c <configfile>' % (self.name,))
            sys.exit(2)

        for opt, arg in opts:
            if opt == '-h':
                print (self.name + ' -c <configfile>')
                sys.exit()
            elif opt in ("-c", "--config"):
                self.configfile = arg
        for arg in odooargs:
            print ('un-nedeed argument %s' % (str(arg),))

        #******
        # config parsing

        self.configParsed = False
        if parseConfig:
            # Parses configuration only if not yet done
            self.parseConfig()


        # *************************************************************
        # Odoo related variables (connection or embedded)
        #
        
        if parseConfig:
            self.dbname = self.getConfigValue("db_name")
        self.odooConn = None
        self.env = None
        self.cr = None

        odooargs = []
        self.odooargs = odooargs

    # *************************************************************
    # Log file configuration
    
    def init_logs(self):
        
        INTERACTIVE = False
        DEBUG = False
        
        if self.config != None:
            INTERACTIVE = (self.config.get("INTERACTIVE", 0) == '1')
            DEBUG = (self.config.get("DEBUG", 0) == '1')

        if self.logger != None:
            if self.logger_ch != None:
                self.logger.removeHandler(self.logger_ch)
                self.logger_ch.close()
            if self.logger_fh != None:
                self.logger.removeHandler(self.logger_fh)
                self.logger_fh.close()
        else:
            logging.basicConfig(level=logging.INFO, format='%(relativeCreated)6d %(threadName)s %(message)s')
            # Logging configuration
            self.logger = logging.getLogger(self.name)

        # sur la console

        ch = logging.StreamHandler()
        formatter = logging.Formatter(FORMAT_CONSOLE)
        ch.setFormatter(formatter)
        self.logger_ch = ch
        self.logger.addHandler(ch)

        # fichier de log
        output_dir = self.getConfigValue("output_directory")  
        fh = None
        if output_dir != None:
            logpath = +os.path.sep + "LOG" + os.path.sep
            filename_TS = datetime.datetime.now().strftime("%Y-%m-%d")
            fh = logging.FileHandler(filename=logpath + self.name + '_' + filename_TS + '.log', mode='w')
            fh.setLevel(level=logging.INFO)

            formatter = logging.Formatter(FORMAT_FIC)
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
        else:
            self.logger.error("Not able to find output_directory %s" % (str(output_dir),))
        self.logger_fh = fh


        if DEBUG:
            self.logger.setLevel(logging.INFO)
            ch.setLevel(logging.DEBUG)
            if fh:
                fh.setLevel(logging.DEBUG)
        elif INTERACTIVE:
            self.logger.setLevel(logging.WARNING)
            ch.setLevel(logging.INFO)
            if fh:
                fh.setLevel(logging.INFO)
        else:
            self.logger.setLevel(logging.ERROR)
            ch.setLevel(logging.ERROR)
            if fh:
                fh.setLevel(logging.ERROR)

    # *************************************************************
    # Utils to get values from config
    def getConfigValue(self, name):
        if (self.config != None):
            return self.config.get(name)
        else:
            return None

    # *************************************************************
    # parse config args and files

    def parseConfig(self, aConfigfile=None):
        
        if aConfigfile != None:
            self.configfile = aConfigfile
        
        if self.configfile == None :
            self.logger.error ('USAGE : \n\t' + self.name + ' -c <configfile>')
            sys.exit(1)


        if not os.path.isfile(self.configfile):
            self.logger.error  ("ERROR: Given Config file is not a file or path is not correct : %s\n" % (str(self.configfile),))
            self.logger.error  ('USAGE: \n\t %s.py -c <configfile>' % (self.name,))
            self.config = None
        
        if self.config == None:
                try:
                    
                    self.config = ConfigObj(self.configfile)
                except:
                    print ("ERROR: Cannot parse config file, syntax error (%s)" % (self.configfile,))
                    return None
        else:
            self.logger.warning("Configuration has already been processed")

    #********************************************************************************
    # Exectute main self script after connecting to an actual odoo Server

    def runWithRemoteOdoo(self):


        self.odooargs = []
        if odoo != False and self.config != None:
            self.odooargs.append("-c" + self.getConfigValue("odoo_config"))
            self.odooargs.append("-d" + self.dbname)
            self.odooargs.append("--db_host=" + self.getConfigValue("db_host"))
            self.odooargs.append("-r" + self.getConfigValue("db_username"))
            self.odooargs.append("-w" + self.getConfigValue("db_password"))
            
        #******************************************************************
        # Gets Connections

        self.odooConn = OdooConnection.Connection(self)
        self.odooConn.getXMLRPCConnection()
        self.run()

    #********************************************************************************************
    # Exectute main self script after starting an embedded Odoo Server

    def runInOdooContext(self):
        
        if self.config != None:
            self.dbname = self.getConfigValue("db_name")

        if self.dbname != None and odoo != False:
            self.logger.info("CONNECTING TO DB : " + self.dbname)

            config.parse_config(self.odooargs)
            odoo.cli.server.report_configuration()

            with odoo.api.Environment.manage():
                registry = odoo.registry(self.dbname)
                odoo.modules.load_modules(registry)
                self.cr = registry.cursor()
                uid = odoo.SUPERUSER_ID
                ctx = odoo.api.Environment(self.cr, uid, {})['res.users'].context_get()
                self.env = odoo.api.Environment(self.cr, uid, ctx)

                self.run()

                self.cr.commit()
                self.cr.close()

        else:
            self.logger.error("NO DB NAME given or No Odoo installation provided")

    #********************************************************************************
    # Main Processing Method

    def run(self):

        #******************************************************************
        # Gets Connection

        print("Default implementation does nothing")
  
