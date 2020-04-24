# -*- coding: utf-8 -*-

"""
Created on march 2018

Utility functions to convert data


@author: C. Guychard
@copyright: ©2018-2020 Article714
@license: AGPL
"""

import copy
import logging
import sys
import xmlrpc.client as xmlrpclib

from .stringconverters import to_string


try:
    import pgdb

    PGDB = "connect" in dir(
        pgdb
    )  # may have confusion between PyGreSQL et pgdb modules :(
except ImportError:
    PGDB = False
    logging.warning(
        "error on import PGDB module => cannot connect locally to POSTGRESQL "
    )


# *****************************
# CONSTANTS
ALL_INSTANCES_FILTER = (
    u"|",
    (u"active", u"=", True),
    (u"active", u"!=", True),
)

ODOO_DATE_FMT = "%Y-%m-%d %H:%M:%S"  # '2018-03-01 11:50:17'


# *****************************
class Connection:
    """
    Abstraction for a Connection to an distant Odoo server
    """

    # *************************************************************
    # constructor
    # parameter script must be an instance of odooscript
    def __init__(self, ctx):
        self.context = ctx
        self.odoo_context = None
        # xmlrpc connection
        self.xmlrpc_uid = None
        self.xmlrpc_models = None
        self.srv_ver = None

        if ctx is not None:
            self.logger = ctx.logger
        else:
            self.logger = logging.getLogger(__name__)

    # *************************************************************
    def get_odoo_xmlrpc_connection(self):  # pylint: disable=too-many-branches
        """
        gets a New XMLRPC connection to odoo
        """

        if self.xmlrpc_uid is not None:
            return (self.xmlrpc_uid, self.xmlrpc_models)

        odoo_host = self.context.get_config_value("odoo_host")
        odoo_port = self.context.get_config_value("odoo_port")
        if odoo_host is not None and odoo_port is not None:
            if odoo_port == "443":
                url = "https://" + odoo_host
            else:
                url = (
                    "http://"
                    + odoo_host
                    + ":"
                    + self.context.get_config_value("odoo_port")
                )
            odoo_username = self.context.get_config_value("odoo_username")
        else:
            self.logger.error("no connection information provided")
            return None

        # *************************************************************
        # establish xmlrpc link
        # http://www.odoo.com/documentation/9.0/api_integration.html

        dbproxy = xmlrpclib.ServerProxy(
            "{}/xmlrpc/db".format(url), allow_none=True
        )

        self.srv_ver = float(dbproxy.server_version().split("-")[0])
        self.logger.info(
            " Connected to odoo server version %s", str(self.srv_ver)
        )

        if self.srv_ver > 8.0:
            common = xmlrpclib.ServerProxy(
                "{}/xmlrpc/2/common".format(url), allow_none=True
            )
        else:
            common = xmlrpclib.ServerProxy(
                "{}/xmlrpc/common".format(url), allow_none=True
            )

        try:
            common.version()
        except xmlrpclib.Fault as err:
            self.logger.exception("Cannot get Odoo version! %s", str(err))
            return None

        lang = self.context.get_config_value("language")
        if lang is not None:
            self.odoo_context = {
                "lang": self.context.get_config_value("language")
            }
        else:
            self.odoo_context = {"lang": "fr_FR"}

        try:
            uid = common.authenticate(
                self.context.get_config_value("db_name"),
                self.context.get_config_value("odoo_username"),
                self.context.get_config_value("odoo_password"),
                self.odoo_context,
            )
        except xmlrpclib.Fault as err:
            self.logger.error(
                "Cannot get authenticated against Odoo server! %s", str(err)
            )
            return None

        if self.srv_ver > 8.0:
            odoo_models = xmlrpclib.ServerProxy(
                "{}/xmlrpc/2/object".format(url), allow_none=True, verbose=0
            )
        else:
            odoo_models = xmlrpclib.ServerProxy(
                "{}/xmlrpc/object".format(url), allow_none=True, verbose=0
            )

        if not uid:
            self.logger.error(
                "ERROR: Not able to connect to Odoo with given information"
                ", username: %s",
                odoo_username,
            )
            sys.exit(1)

        self.xmlrpc_uid = uid
        self.xmlrpc_models = odoo_models

        return (uid, odoo_models)

    # *************************************************************
    def get_db_connection(self):
        """
        gets a New Postgresql connection to odoo
        """
        db_name = self.context.get_config_value("db_name")

        if PGDB:
            # *************************************************************
            # connect to Db
            ldsn = self.context.get_config_value("db_host") + ":5432"
            if self.context.get_config_value("db_local") == "1":
                return pgdb.connect(
                    database=db_name,
                    user=self.context.get_config_value("db_username"),
                )

            if self.context.get_config_value("db_password") is not None:
                return pgdb.connect(
                    database=db_name,
                    dsn=ldsn,
                    user=self.context.get_config_value("db_username"),
                    password=self.context.get_config_value("db_password"),
                )

            return pgdb.connect(
                database=db_name,
                dsn=ldsn,
                user=self.context.get_config_value("db_username"),
            )
        logging.error("No PGDB module")
        return None

    # *************************************************************************
    def odoo_search_create_or_write(  # pylint: disable=too-many-arguments,dangerous-default-value,too-many-branches
        self,
        model_name,
        search_criteria=[],
        values={},
        create_only=False,
        can_be_archived=False,
    ):
        """
        helper function to search and create or write if exist
        """
        obj_id = None
        if self.xmlrpc_uid is None:
            self.get_odoo_xmlrpc_connection()
        try:
            if self.xmlrpc_models is None:
                self.logger.error("Not Connected to Odoo Database/Server")
                return None

            result_params = {"offset": 0, "count": False}
            if can_be_archived:
                full_search = copy.copy(search_criteria)
                for val in ALL_INSTANCES_FILTER:
                    full_search.append(val)
                found = self.odoo_search(
                    model_name, full_search, result_params
                )
            else:

                found = self.odoo_search(
                    model_name, search_criteria, result_params
                )

                if found is None:
                    return None

            lfound = len(found)
            # create only if do not exist
            if lfound == 0:
                try:
                    obj_id = self.xmlrpc_models.execute_kw(
                        self.context.get_config_value("db_name"),
                        self.xmlrpc_uid,
                        self.context.get_config_value("odoo_password"),
                        model_name,
                        "create",
                        [values],
                        {"context": self.odoo_context},
                    )
                except xmlrpclib.Fault as err:
                    self.logger.error(
                        "Failed to create record %s [ %s ] %s",
                        model_name,
                        to_string(values),
                        to_string(err),
                    )

            elif lfound == 1:
                obj_id = found[0]["id"]
                try:
                    if not create_only:
                        self.xmlrpc_models.execute_kw(
                            self.context.get_config_value("db_name"),
                            self.xmlrpc_uid,
                            self.context.get_config_value("odoo_password"),
                            model_name,
                            "write",
                            [obj_id, values],
                            {"context": self.odoo_context},
                        )
                except xmlrpclib.Fault as err:
                    self.logger.error(
                        "Failed to write record %s (%s) [%s] -> %s",
                        model_name,
                        to_string(obj_id),
                        to_string(values),
                        to_string(err),
                    )
            else:
                self.logger.warning(
                    "Failed to update record  ( %s ) too many objects found"
                    " for %s",
                    model_name,
                    str(search_criteria),
                )

            return obj_id

        except xmlrpclib.Fault as err:
            self.logger.error(
                "WARN Error when looking for or writing a record for "
                "model: %s [ %s ] %s",
                model_name,
                to_string(values),
                to_string(err),
            )

    # *************************************************************
    def odoo_search(self, model_name, search_conditions, result_parameters):
        """
        Search elements in odoo
        """
        if self.xmlrpc_uid is None:
            self.get_odoo_xmlrpc_connection()
        try:

            if self.xmlrpc_models is not None:
                if result_parameters:
                    result_parameters["context"] = self.odoo_context
                else:
                    result_parameters = {"context": self.odoo_context}

                if self.srv_ver > 8.0:
                    result = self.xmlrpc_models.execute_kw(
                        self.context.get_config_value("db_name"),
                        self.xmlrpc_uid,
                        self.context.get_config_value("odoo_password"),
                        model_name,
                        "search_read",
                        [search_conditions],
                        result_parameters,
                    )
                    return result

                found = self.xmlrpc_models.execute_kw(
                    self.context.get_config_value("db_name"),
                    self.xmlrpc_uid,
                    self.context.get_config_value("odoo_password"),
                    model_name,
                    "search",
                    [search_conditions],
                    {"context": self.odoo_context},
                )
                if found:
                    result = self.xmlrpc_models.execute_kw(
                        self.context.get_config_value("db_name"),
                        self.xmlrpc_uid,
                        self.context.get_config_value("odoo_password"),
                        model_name,
                        "read",
                        [found],
                        {"context": self.odoo_context},
                    )
                    return result
            else:
                self.logger.error("Not Connected to Odoo Database/Server")

            return ()

        except xmlrpclib.Fault:
            logging.exception(
                "WARNING: error when searching for object: %s -> %s",
                model_name,
                str(search_conditions),
            )
            return ()

    # *************************************************************
    def odoo_idsearch(self, model_name, search_conditions):
        """
        Search id of elements in odoo with language support enabled
        """
        if self.xmlrpc_uid is None:
            self.get_odoo_xmlrpc_connection()
        try:
            result = None
            if self.xmlrpc_models is not None:
                result = self.xmlrpc_models.execute_kw(
                    self.context.get_config_value("db_name"),
                    self.xmlrpc_uid,
                    self.context.get_config_value("odoo_password"),
                    model_name,
                    "search",
                    [search_conditions],
                    {"context": self.odoo_context},
                )

            return result
        except xmlrpclib.Fault:
            logging.exception(
                "     WARNING: error when searching for object: %s -> %s",
                model_name,
                str(search_conditions),
            )
            return ()

    # *************************************************************
    def odoo_read(self, model_name, ids):
        """
        Read elements in odoo
        """
        if self.xmlrpc_uid is None:
            self.get_odoo_xmlrpc_connection()

        try:
            result = self.xmlrpc_models.execute_kw(
                self.context.get_config_value("db_name"),
                self.xmlrpc_uid,
                self.context.get_config_value("odoo_password"),
                model_name,
                "read",
                [ids],
                {"context": self.odoo_context},
            )
            return result

        except xmlrpclib.Fault as err:
            self.logger.error(
                "     WARNING: error when reading  object: %s -> %s",
                model_name,
                str(ids),
            )
            self.logger.error(
                "                    MSG: %s -> %s",
                err.faultCode,
                "".join(err.faultString.split("\n")[-2:]),
            )
            return None

    # *************************************************************
    def odoo_write(self, model_name, obj_id, values):
        """
        Update element in odoo   // Single Object
        """
        if self.xmlrpc_uid is None:
            self.get_odoo_xmlrpc_connection()
        try:
            result = self.xmlrpc_models.execute_kw(
                self.context.get_config_value("db_name"),
                self.xmlrpc_uid,
                self.context.get_config_value("odoo_password"),
                model_name,
                "write",
                [obj_id, values],
                {"context": self.odoo_context},
            )
            return result
        except xmlrpclib.Fault as err:
            self.logger.error(
                "     WARNING: error when writing object: %s -> %s ",
                model_name,
                str(values),
            )
            self.logger.error(
                "                    MSG: %s -> %s",
                err.faultCode,
                "".join(err.faultString.split("\n")[-2:]),
            )
            return None

    # *************************************************************
    # Create  new element in odoo   // Single Object
    def odoo_create(self, model_name, *values):
        """
        Create a new record
        """
        if self.xmlrpc_uid is None:
            self.get_odoo_xmlrpc_connection()
        try:
            result = self.xmlrpc_models.execute_kw(
                self.context.get_config_value("db_name"),
                self.xmlrpc_uid,
                self.context.get_config_value("odoo_password"),
                model_name,
                "create",
                [values],
                {"context": self.odoo_context},
            )
            return result
        except xmlrpclib.Fault as err:
            self.logger.error(
                "     WARNING: error when creating object: %s -> %s",
                model_name,
                str(values),
            )
            self.logger.error(
                "                    MSG: %s -> %s",
                err.faultCode,
                "".join(err.faultString.split("\n")[-2:]),
            )
            return None

    # *************************************************************
    def odoo_delete(self, model_name, obj_ids):
        """
        Deletes  new element in odoo
        """
        if self.xmlrpc_uid is None:
            self.get_odoo_xmlrpc_connection()
        try:
            result = False
            if isinstance(obj_ids, (tuple, list)):
                result = self.xmlrpc_models.execute_kw(
                    self.context.get_config_value("db_name"),
                    self.xmlrpc_uid,
                    self.context.get_config_value("odoo_password"),
                    model_name,
                    "unlink",
                    [obj_ids],
                    {"context": self.odoo_context},
                )
            elif isinstance(obj_ids, int):
                result = self.xmlrpc_models.execute_kw(
                    self.context.get_config_value("db_name"),
                    self.xmlrpc_uid,
                    self.context.get_config_value("odoo_password"),
                    model_name,
                    "unlink",
                    [[obj_ids]],
                    {"context": self.odoo_context},
                )
            return result
        except xmlrpclib.Fault as err:
            self.logger.warning(
                "     WARNING: error when deleting object: %s -> %s",
                model_name,
                str(obj_ids),
            )
            self.logger.warning(
                "                    MSG: %s -> %s",
                err.faultCode,
                "".join(err.faultString.split("\n")[-2:]),
            )
            return None

    # *************************************************************
    # Execute stuff in odoo   // Single Object
    def odoo_execute(self, model_name, method_name, obj_ids, parameters):
        """
        Run execute_kw
        """
        if self.xmlrpc_uid is None:
            self.get_odoo_xmlrpc_connection()
        try:
            result = False
            if isinstance(obj_ids, (tuple, list)):
                result = self.xmlrpc_models.execute_kw(
                    self.context.get_config_value("db_name"),
                    self.xmlrpc_uid,
                    self.context.get_config_value("odoo_password"),
                    model_name,
                    method_name,
                    [obj_ids, parameters],
                    {"context": self.odoo_context},
                )
            elif isinstance(obj_ids, int):
                result = self.xmlrpc_models.execute_kw(
                    self.context.get_config_value("db_name"),
                    self.xmlrpc_uid,
                    self.context.get_config_value("odoo_password"),
                    model_name,
                    method_name,
                    [[obj_ids], parameters],
                    {"context": self.odoo_context},
                )
            return result
        except xmlrpclib.Fault as err:
            self.logger.error(
                "     WARNING: error when executing %s on object: %s -> %s",
                method_name,
                model_name,
                str(parameters),
            )
            self.logger.error(
                "                    MSG: %s-> %s",
                err.faultCode,
                "".join(err.faultString.split("\n")[-2:]),
            )
            return None
