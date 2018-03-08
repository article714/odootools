# -*- coding: utf-8 -*-

'''
Created on march 2018

Utility functions to convert data


@author: C. Guychard
@copyright: ©2018 Article714
@license: AGPL
'''

from configobj import ConfigObj
import datetime
import getopt
import logging
import os.path
import sys

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
# Odoo Script
class Script:
    '''
    A generic Class to capitalize technical stuffs
    '''
    config = None
    name = 'Generic OdooScript script'

    def run(self):

        #******************************************************************
        # Gets Connection

        print "Default implementation does nothing"

    #********************************************************************************
    # Exectute main self script after connecting to an actual odoo Server

    def runWithRemoteOdoo(self):

        #******************************************************************
        # Gets Connections

        self.odooConn = OdooConnection.Connection(self)
        self.odooConn.getXMLRPCConnection()
        self.run()

    #********************************************************************************************
    # Exectute main self script after starting an embedded Odoo Server

    def runInOdooContext(self):

        if self.dbname != None:
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
            self.logger.error("NO DB NAME given")

    # *************************************************************
    # Utils to get values from config
    def getConfigValue(self, name):
        if (self.config != None):
            return self.config.get(name)
        else:
            return None

    # *************************************************************
    # parse config args and files

    def parseConfig(self):
        configfile = None

        try:
            opts, odooargs = getopt.getopt(sys.argv[1:], "hc:", ["config="])
        except getopt.GetoptError:
            print 'USAGE : \n\t' + self.name + '.py -c <configfile>'
            sys.exit(2)

        for opt, arg in opts:
            if opt == '-h':
                print 'translate_to_odoo.py -c <configfile>'
                sys.exit()
            elif opt in ("-c", "--config"):
                configfile = arg
        for arg in odooargs:
            print 'un-nedeed argument' + str(arg)

        if configfile == None :
            print 'USAGE : \n\t' + self.name + ' -c <configfile>'
            sys.exit(1)

        if not os.path.isfile(configfile):
            print "ERROR: Given Config file is not a file or path is not correct\n"
            print 'USAGE: \n\t translate_to_odoo.py -c <configfile>'
            self.config = None

        try:
            self.config = ConfigObj(configfile)
        except:
            print "ERROR: Cannot parse config file, syntax error (" + configfile + ")"
            return None

    # *************************************************************
    # Constructor, passing arguments from the command line

    def __init__(self):
        '''
        Constructor that uses command line arguments to build a config object
        '''

        self.name = os.path.basename(sys.argv[0]).replace('.py', '')

        # Parses configuration only if not yet done
        self.parseConfig()

        #******
        # Logging configuration

        logging.basicConfig(level = logging.INFO, format = '%(relativeCreated)6d %(threadName)s %(message)s')

        # Logging configuration
        FORMAT_CONSOLE = '%(levelname)s - %(message)s'
        FORMAT_FIC = '%(asctime)s - %(levelname)s - %(message)s'
        logger = logging.getLogger(self.name)

        self.logger = logger
        INTERACTIVE = False
        DEBUG = False
        if self.config != None:
            INTERACTIVE = (self.config.get("INTERACTIVE", 0) == '1')
            DEBUG = (self.config.get("DEBUG", 0) == '1')

        # sur la console

        ch = logging.StreamHandler()
        formatter = logging.Formatter(FORMAT_CONSOLE)
        ch.setFormatter(formatter)
        self.logger_ch = ch

        # fichier de log
        logpath = self.getConfigValue("output_directory") + os.path.sep + "LOG" + os.path.sep
        filename_TS = datetime.datetime.now().strftime("%Y-%m-%d")
        fh = logging.FileHandler(filename = logpath + self.name + '_' + filename_TS + '.log', mode = 'w')
        fh.setLevel(level = logging.INFO)
        self.logger_fh = fh

        formatter = logging.Formatter(FORMAT_FIC)
        fh.setFormatter(formatter)

        logger.addHandler(ch)
        logger.addHandler(fh)

        if DEBUG:
            logger.setLevel(logging.INFO)
            ch.setLevel(logging.DEBUG)
            fh.setLevel(logging.DEBUG)
        elif INTERACTIVE:
            logger.setLevel(logging.WARNING)
            ch.setLevel(logging.INFO)
            fh.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.ERROR)
            ch.setLevel(logging.ERROR)
            fh.setLevel(logging.ERROR)

        # *************************************************************
        # Odoo related variables (connection or embedded)
        #

        self.dbname = self.getConfigValue("db_name")
        self.odooConn = None
        self.env = None
        self.cr = None

        odooargs = []
        if odoo != False:
            odooargs.append("-c" + self.getConfigValue("odoo_config"))
            odooargs.append("-d" + self.dbname)
            odooargs.append("--db_host=" + self.getConfigValue("db_host"))
            odooargs.append("-r" + self.getConfigValue("db_username"))
            odooargs.append("-w" + self.getConfigValue("db_password"))

        self.odooargs = odooargs

