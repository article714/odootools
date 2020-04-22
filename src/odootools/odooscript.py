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
from abc import ABCMeta, abstractmethod

from configobj import ConfigObj, ConfigObjError

from . import odooconnection

try:
    import odoo

    ODOO_OK = True
except (ModuleNotFoundError, ImportError):
    ODOO_OK = False
    logging.error("error on Odoo import")

try:
    from odoo.tools import config
except (ModuleNotFoundError, ImportError):
    ODOO_OK = False
    logging.error("ImportError: config from odoo.tools")

# ************************************************
#  CONSTANTS

FORMAT_CONSOLE = "%(levelname)s - %(message)s"
FORMAT_FIC = "%(asctime)s - %(levelname)s - %(message)s"

# ************************************************
# Odoo Script


class AbstractOdooScript(
    metaclass=ABCMeta
):  # pylint: disable=too-many-instance-attributes
    """
    A generic Class to capitalize technical stuffs and ease the writings
    of scripts for Odoo
    """

    # *************************************************************
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
            format="%(asctime)s :: %(levelname)s :: %(name)s :: %(threadName)s :: %(message)s",
        )

        # Logging configuration
        self.logger = logging.getLogger(self.name)
        self.log_handlers = []

        self.configfile = None
        self.config = None

        # ******
        # args parsing
        self._parse_args()

        # ******
        # config parsing

        if parse_config:
            # Parses configuration only if not yet done
            self.parse_config()

        # *************************************************************
        # Odoo related variables (connection or embedded)
        #

        if self.config:
            self.dbname = self.get_config_value("db_name")

        self.connection = None
        self.env = None
        self.cursor = None

        odooargs = []
        self.odooargs = odooargs

    # *************************************************************
    def _parse_args(self):
        """
        Command line args
        """
        try:
            opts, unneededargs = getopt.getopt(
                sys.argv[1:], "hc:", ["config="]
            )
        except getopt.GetoptError:
            self.logger.error("USAGE : \n\t %s.py -c <configfile>", self.name)
            sys.exit(2)

        for opt, arg in opts:
            if opt == "-h":
                print(  # pylint: disable=print-used
                    self.name + " -c <configfile>"
                )
                sys.exit()
            elif opt in ("-c", "--config"):
                self.configfile = arg
        for arg in unneededargs:
            self.logger.warning("un-nedeed argument %s", str(arg))

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
            for handlr in self.log_handlers:
                self.logger.removeHandler(handlr)
                handlr.close()
            self.log_handlers = []

        else:
            logging.basicConfig(
                level=logging.INFO,
                format="%(relativeCreated)6d %(threadName)s %(message)s",
            )
            # Logging configuration
            self.logger = logging.getLogger(self.name)

        # sur la console

        console_hdlr = logging.StreamHandler()
        formatter = logging.Formatter(FORMAT_CONSOLE)
        console_hdlr.setFormatter(formatter)
        self.log_handlers.append(console_hdlr)
        self.logger.addHandler(console_hdlr)

        # fichier de log
        output_dir = self.get_config_value("output_directory")
        file_hdlr = None
        if output_dir is not None:
            logpath = output_dir + os.path.sep
            filename_ts = datetime.datetime.now().strftime("%Y-%m-%d")
            file_hdlr = logging.FileHandler(
                filename=f"{logpath}{self.name}_{filename_ts}.log", mode="w",
            )
            file_hdlr.setLevel(level=logging.INFO)

            formatter = logging.Formatter(FORMAT_FIC)
            file_hdlr.setFormatter(formatter)
            self.logger.addHandler(file_hdlr)
        else:
            self.logger.error(
                "Not able to find output_directory %s", str(output_dir)
            )
        self.log_handlers.append(file_hdlr)

        if debug:
            self.logger.setLevel(logging.INFO)
            console_hdlr.setLevel(logging.DEBUG)
            if file_hdlr:
                file_hdlr.setLevel(logging.DEBUG)
        elif interactive:
            self.logger.setLevel(logging.WARNING)
            console_hdlr.setLevel(logging.INFO)
            if file_hdlr:
                file_hdlr.setLevel(logging.INFO)
        else:
            self.logger.setLevel(logging.ERROR)
            console_hdlr.setLevel(logging.ERROR)
            if file_hdlr:
                file_hdlr.setLevel(logging.ERROR)

    # *************************************************************
    def get_config_value(self, name, default=None):
        """
        Utils to get values from config
        """
        if self.config is not None:
            return self.config.get(name, default)
        return None

    # *************************************************************
    def parse_config(self, configfile=None):
        """
        parse config args and files
        """

        if configfile is not None:
            self.configfile = configfile

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
            sys.exit(1)

        if self.config is None:
            try:

                self.config = ConfigObj(self.configfile)
            except ConfigObjError:
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

        self.connection = odooconnection.Connection(self)
        self.connection.get_odoo_xmlrpx_connection()
        self.run()

    # *************************************************************************
    def run_in_odoo_context(self):
        """
        Execute main self script after starting an embedded Odoo Server
        """
        self.init_logs()

        self.odooargs = []
        if ODOO_OK and self.config is not None:

            self.dbname = self.get_config_value("db_name")

            if self.dbname is not None and ODOO_OK:
                self.logger.info("CONNECTING TO DB : %s", {self.dbname})

            if ODOO_OK and self.config is not None:
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
                self.cursor = registry.cursor()
                uid = odoo.SUPERUSER_ID
                ctx = odoo.api.Environment(self.cursor, uid, {})[
                    "res.users"
                ].context_get()
                self.env = odoo.api.Environment(self.cursor, uid, ctx)

                self.run()

                self.cursor.commit()
                self.cursor.close()

        else:
            self.logger.error(
                "NO DB NAME given or No Odoo installation provided"
            )

    # ************************************************************************

    @abstractmethod
    def run(self):
        """
        Main Processing Method
        """
