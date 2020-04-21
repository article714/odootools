# -*- coding: utf-8 -*-

"""
Created on march 2018

Utility functions to convert data


@author: C. Guychard
@copyright: ©2018 Article714
@license: AGPL
"""

import datetime
import getopt
import logging
import os.path
import sys

from configobj import ConfigObj

from . import odooconnection

try:
    import odoo
except Exception:
    odoo = None
    logging.error("error on Odoo import")

try:
    from odoo.tools import config
except Exception:
    config = False

# ************************************************
#  CONSTANTS


FORMAT_CONSOLE = "%(levelname)s - %(message)s"
FORMAT_FIC = "%(asctime)s - %(levelname)s - %(message)s"

# ************************************************
# Odoo Script


class Script(object):
    """
    A generic Class to capitalize technical stuffs and ease the writings
    of scripts for Odoo
    """

    config = None

    # *************************************************************
    # Constructor, passing arguments from the command line

    def __init__(self, parse_config=True):
        """
        Constructor that uses command line arguments to build a config object
        """

        if len(sys.argv) > 1:
            self.name = os.path.basename(sys.argv[0]).replace(".py", "")
        else:
            self.name = "Generic odooscript script"

        # ******
        # Basic Logging configuration

        logging.basicConfig(
            level=logging.INFO,
            format="%(relativeCreated)6d %(threadName)s %(message)s",
        )

        # Logging configuration
        self.logger = logging.getLogger(self.name)
        self.logger_ch = None
        self.logger_fh = None

        # ******
        # args parsing

        self.configfile = None
        self.config = None
        try:
            opts, unneededargs = getopt.getopt(
                sys.argv[1:], "hc:", ["config="]
            )
        except getopt.GetoptError:
            self.logger.error("USAGE : \n\t %s.py -c <configfile>", self.name)
            sys.exit(2)

        for opt, arg in opts:
            if opt == "-h":
                print(
                    self.name + " -c <configfile>"
                )  # pylint: disable=print-used
                sys.exit()
            elif opt in ("-c", "--config"):
                self.configfile = arg
        for arg in unneededargs:
            print("un-nedeed argument %s" % (str(arg),))

        # ******
        # config parsing

        self.configParsed = False
        if parse_config:
            # Parses configuration only if not yet done
            self.parse_config()

        # *************************************************************
        # Odoo related variables (connection or embedded)
        #

        if parse_config:
            self.dbname = self.get_config_value("db_name")
        self.odooConn = None
        self.env = None
        self.cr = None

        odooargs = []
        self.odooargs = odooargs

    # *************************************************************
    def init_logs(self):
        """
        Log file configuration
        """

        interactive = False
        debug = False

        if self.config is not None:
            interactive = self.config.get("INTERACTIVE", 0) == "1"
            debug = self.config.get("DEBUG", 0) == "1"

        if self.logger is not None:
            if self.logger_ch is not None:
                self.logger.removeHandler(self.logger_ch)
                self.logger_ch.close()
            if self.logger_fh is not None:
                self.logger.removeHandler(self.logger_fh)
                self.logger_fh.close()
        else:
            logging.basicConfig(
                level=logging.INFO,
                format="%(relativeCreated)6d %(threadName)s %(message)s",
            )
            # Logging configuration
            self.logger = logging.getLogger(self.name)

        # sur la console

        ch = logging.StreamHandler()
        formatter = logging.Formatter(FORMAT_CONSOLE)
        ch.setFormatter(formatter)
        self.logger_ch = ch
        self.logger.addHandler(ch)

        # fichier de log
        output_dir = self.get_config_value("output_directory")
        fh = None
        if output_dir is not None:
            logpath = output_dir + os.path.sep
            filename_TS = datetime.datetime.now().strftime("%Y-%m-%d")
            fh = logging.FileHandler(
                filename=logpath + self.name + "_" + filename_TS + ".log",
                mode="w",
            )
            fh.setLevel(level=logging.INFO)

            formatter = logging.Formatter(FORMAT_FIC)
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
        else:
            self.logger.error(
                "Not able to find output_directory %s", str(output_dir)
            )
        self.logger_fh = fh

        if debug:
            self.logger.setLevel(logging.INFO)
            ch.setLevel(logging.DEBUG)
            if fh:
                fh.setLevel(logging.DEBUG)
        elif interactive:
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
    def get_config_value(self, name, default=None):
        """
        Utils to get values from config
        """
        if self.config is not None:
            return self.config.get(name, default)
        else:
            return None

    # *************************************************************
    def parse_config(self, aConfigfile=None):
        """
        parse config args and files
        """

        if aConfigfile is not None:
            self.configfile = aConfigfile

        if self.configfile is None:
            self.logger.error("USAGE : \n\t %s -c <configfile>", self.name)
            sys.exit(1)

        if not os.path.isfile(self.configfile):
            self.logger.error(
                "ERROR: Given Config file is not a file or path "
                "is not correct : %s\n",
                str(self.configfile),
            )
            self.logger.error("USAGE: \n\t %s.py -c <configfile>", self.name)
            self.config = None

        if self.config is None:
            try:

                self.config = ConfigObj(self.configfile)
            except Exception:
                self.logger.error(
                    "ERROR: Cannot parse config file, syntax error (%s)",
                    self.configfile,
                )
        else:
            self.logger.warning("Configuration has already been processed")

    # *************************************************************************
    def run_with_remote_odoo(self):
        """
        Execute main self script after connecting to an actual odoo Server
        """

        self.init_logs()

        # ******************************************************************
        # Gets Connections

        self.odooConn = odooconnection.Connection(self)
        self.odooConn.getXMLRPCConnection()
        self.run()

    # *************************************************************************
    def run_in_odoo_context(self):
        """
        Execute main self script after starting an embedded Odoo Server
        """
        self.init_logs()

        self.odooargs = []
        if odoo is not False and self.config is not None:

            self.dbname = self.get_config_value("db_name")

            if self.dbname is not None and odoo is not False:
                self.logger.info("CONNECTING TO DB : %s", {self.dbname})

            if odoo is not False and self.config is not None:
                self.odooargs.append(
                    "-c" + self.get_config_value("odoo_config")
                )
                self.odooargs.append("-d" + self.dbname)
                self.odooargs.append(
                    "--db_host=" + self.get_config_value("db_host")
                )
                self.odooargs.append(
                    "-r" + self.get_config_value("db_username")
                )
                self.odooargs.append(
                    "-w" + self.get_config_value("db_password")
                )

            config.parse_config(self.odooargs)

            odoo.cli.server.report_configuration()

            with odoo.api.Environment.manage():
                registry = odoo.registry(self.dbname)
                odoo.modules.load_modules(registry)
                self.cr = registry.cursor()
                uid = odoo.SUPERUSER_ID
                ctx = odoo.api.Environment(self.cr, uid, {})[
                    "res.users"
                ].context_get()
                self.env = odoo.api.Environment(self.cr, uid, ctx)

                self.run()

                self.cr.commit()
                self.cr.close()

        else:
            self.logger.error(
                "NO DB NAME given or No Odoo installation provided"
            )

    # ************************************************************************
    def run(self):
        """
        Main Processing Method
        """

        # ******************************************************************
        # Gets Connection

        self.logger.warning(
            "Default implementation does nothing in %s", self.name
        )
