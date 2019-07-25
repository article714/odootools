# -*- coding: utf-8 -*-

"""
Created on march 2018

Utility functions to convert data


@author: C. Guychard
@copyright: ©2018 Article714
@license: AGPL
"""

import copy
import logging
import sys
import xmlrpc.client as xmlrpclib

from .StringConverters import toString


try:
    import pgdb
except:
    pgdb = False
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
# Main Classes
class Connection(object):

    # *************************************************************
    # constructor
    # parameter script must be an instance of OdooScript
    def __init__(self, ctx):
        self.context = ctx
        # xmlrpc connection
        self.xmlrpc_uid = None
        self.xmlrpc_models = None
        self.srv_ver = None

        if ctx != None:
            self.logger = ctx.logger
        else:
            self.logger = logging.getLogger(__name__)

    # *************************************************************
    # gets a New XMLRPC connection to odoo
    def getXMLRPCConnection(self):

        if self.xmlrpc_uid != None:
            return (self.xmlrpc_uid, self.xmlrpc_models)

        odoo_host = self.context.getConfigValue("odoo_host")
        odoo_port = self.context.getConfigValue("odoo_port")
        if odoo_host != None and odoo_port != None:
            if odoo_port == "443":
                url = "https://" + odoo_host
            else:
                url = (
                    "http://"
                    + odoo_host
                    + ":"
                    + self.context.getConfigValue("odoo_port")
                )
            odoo_username = self.context.getConfigValue("odoo_username")
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
            " Connected to odoo server version %s" % str(self.srv_ver)
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
            v = common.version()
        except Exception as e:
            self.logger.exception("Paf! %s" % str(e))
            return None

        lang = self.context.getConfigValue("language")
        if lang != None:
            self.odoo_context = {
                "lang": self.context.getConfigValue("language")
            }
        else:
            self.odoo_context = {"lang": "fr_FR"}

        uid = common.authenticate(
            self.context.getConfigValue("db_name"),
            self.context.getConfigValue("odoo_username"),
            self.context.getConfigValue("odoo_password"),
            self.odoo_context,
        )

        if self.srv_ver > 8.0:
            odoo_models = xmlrpclib.ServerProxy(
                "{}/xmlrpc/2/object".format(url), allow_none=True, verbose=0
            )
        else:
            odoo_models = xmlrpclib.ServerProxy(
                "{}/xmlrpc/object".format(url), allow_none=True, verbose=0
            )

        if not uid:
            print(
                "ERROR: Not able to connect to Odoo with given information, username: "
                + odoo_username
            )
            sys.exit(1)

        self.xmlrpc_uid = uid
        self.xmlrpc_models = odoo_models

        return (uid, odoo_models)

    # *************************************************************
    # gets a New Postgresql connection to odoo
    def getDBConnection(self):
        db_name = self.context.getConfigValue("db_name")

        if pgdb:
            # *************************************************************
            # connect to Db
            ldsn = self.context.getConfigValue("db_host") + ":5432"
            if self.context.getConfigValue("db_local") == "1":
                return pgdb.connect(
                    database=db_name,
                    user=self.context.getConfigValue("db_username"),
                )
            else:
                if self.context.getConfigValue("db_password") != None:
                    return pgdb.connect(
                        database=db_name,
                        dsn=ldsn,
                        user=self.context.getConfigValue("db_username"),
                        password=self.context.getConfigValue("db_password"),
                    )
                else:
                    return pgdb.connect(
                        database=db_name,
                        dsn=ldsn,
                        user=self.context.getConfigValue("db_username"),
                    )
        else:
            logging.error("No PGDB module")

    # *************************************************************************
    # helper function to search and create or write if exist

    def odoo_search_create_or_write(
        self,
        model_name,
        search_criteria=[],
        values={},
        create_only=False,
        can_be_archived=False,
    ):
        obj_id = None
        if self.xmlrpc_uid == None:
            self.getXMLRPCConnection()
        try:
            if can_be_archived:
                full_search = copy.copy(search_criteria)
                for val in ALL_INSTANCES_FILTER:
                    full_search.append(val)
                found = self.odoo_search(
                    model_name, full_search, [0, 0, False, False]
                )
            else:

                found = self.odoo_search(
                    model_name, search_criteria, [0, 0, False, False]
                )

            lfound = len(found)
            # create only if do not exist
            if lfound == 0:
                try:
                    obj_id = self.xmlrpc_models.execute_kw(
                        self.context.getConfigValue("db_name"),
                        self.xmlrpc_uid,
                        self.context.getConfigValue("odoo_password"),
                        model_name,
                        "create",
                        [values],
                        {"context": self.odoo_context},
                    )
                except Exception as e:
                    self.logger.error(
                        "Failed to create record "
                        + model_name
                        + " [ "
                        + toString(values)
                        + "] "
                        + toString(e)
                    )

            elif lfound == 1:
                obj_id = found[0]["id"]
                try:
                    if not create_only:
                        result = self.xmlrpc_models.execute_kw(
                            self.context.getConfigValue("db_name"),
                            self.xmlrpc_uid,
                            self.context.getConfigValue("odoo_password"),
                            model_name,
                            "write",
                            [obj_id, values],
                            {"context": self.odoo_context},
                        )
                except Exception as e:
                    self.logger.error(
                        "Failed to write record "
                        + model_name
                        + "("
                        + toString(obj_id)
                        + ") [ "
                        + toString(values)
                        + "] "
                        + toString(e)
                    )
            else:
                self.logger.warning(
                    "Failed to update record  ("
                    + model_name
                    + ") too many objects found for "
                    + str(search_criteria)
                )

            return obj_id

        except Exception as e:
            self.logger.error(
                "WARNING Error when looking for or writing a record for model: "
                + model_name
                + " [ "
                + toString(values)
                + "] "
                + toString(e)
            )

    # *************************************************************
    # Search elements in odoo
    def odoo_search(self, model_name, search_conditions, result_parameters):
        if self.xmlrpc_uid == None:
            self.getXMLRPCConnection()
        try:

            if result_parameters:
                result_parameters["context"] = self.odoo_context
            else:
                result_parameters = {"context": self.odoo_context}

            if self.srv_ver > 8.0:
                result = self.xmlrpc_models.execute_kw(
                    self.context.getConfigValue("db_name"),
                    self.xmlrpc_uid,
                    self.context.getConfigValue("odoo_password"),
                    model_name,
                    "search_read",
                    [search_conditions],
                    result_parameters,
                )
                return result
            else:
                found = self.xmlrpc_models.execute_kw(
                    self.context.getConfigValue("db_name"),
                    self.xmlrpc_uid,
                    self.context.getConfigValue("odoo_password"),
                    model_name,
                    "search",
                    [search_conditions],
                    {"context": self.odoo_context},
                )
                if len(found) > 0:
                    result = self.xmlrpc_models.execute_kw(
                        self.context.getConfigValue("db_name"),
                        self.xmlrpc_uid,
                        self.context.getConfigValue("odoo_password"),
                        model_name,
                        "read",
                        [found],
                        {"context": self.odoo_context},
                    )
                    return result
                else:
                    return ()

        except xmlrpclib.Fault as e:
            logging.exception(
                "WARNING: error when searching for object: "
                + model_name
                + " -> "
                + str(search_conditions)
            )
            return ()

    # *************************************************************
    # Search id of elements in odoo with language support enabled
    def odoo_idsearch(self, model_name, search_conditions):
        if self.xmlrpc_uid == None:
            self.getXMLRPCConnection()
        try:
            result = self.xmlrpc_models.execute_kw(
                self.context.getConfigValue("db_name"),
                self.xmlrpc_uid,
                self.context.getConfigValue("odoo_password"),
                model_name,
                "search",
                [search_conditions],
                {"context": self.odoo_context},
            )

            return result
        except xmlrpclib.Fault as e:
            logging.exception(
                "     WARNING: error when searching for object: "
                + model_name
                + " -> "
                + str(search_conditions)
            )
            return ()

    # *************************************************************
    # Read elements in odoo
    def odoo_read(self, model_name, ids):
        if self.xmlrpc_uid == None:
            self.getXMLRPCConnection()

        try:
            result = self.xmlrpc_models.execute_kw(
                self.context.getConfigValue("db_name"),
                self.xmlrpc_uid,
                self.context.getConfigValue("odoo_password"),
                model_name,
                "read",
                [ids],
                {"context": self.odoo_context},
            )
            return result

        except xmlrpclib.Fault as e:
            print(
                "     WARNING: error when reading  object: "
                + model_name
                + " -> "
                + str(ids)
            )
            print(
                "                    MSG: {0} -> {1}".format(
                    e.faultCode, "".join(e.faultString.split("\n")[-2:])
                )
            )
            return None

    # *************************************************************
    # Update element in odoo   // Single Object
    def odoo_write(self, model_name, obj_id, values):
        if self.xmlrpc_uid == None:
            self.getXMLRPCConnection()
        try:
            result = self.xmlrpc_models.execute_kw(
                self.context.getConfigValue("db_name"),
                self.xmlrpc_uid,
                self.context.getConfigValue("odoo_password"),
                model_name,
                "write",
                [obj_id, values],
                {"context": self.odoo_context},
            )
            return result
        except xmlrpclib.Fault as e:
            print(
                "     WARNING: error when writing object: "
                + model_name
                + " -> "
                + str(values)
            )
            print(
                "                    MSG: {0} -> {1}".format(
                    e.faultCode, "".join(e.faultString.split("\n")[-2:])
                )
            )
            return None

    # *************************************************************
    # Create  new element in odoo   // Single Object
    def odoo_create(self, model_name, *values):
        if self.xmlrpc_uid == None:
            self.getXMLRPCConnection()
        try:
            result = self.xmlrpc_models.execute_kw(
                self.context.getConfigValue("db_name"),
                self.xmlrpc_uid,
                self.context.getConfigValue("odoo_password"),
                model_name,
                "create",
                [values],
                {"context": self.odoo_context},
            )
            return result
        except xmlrpclib.Fault as e:
            print(
                "     WARNING: error when creating object: "
                + model_name
                + " -> "
                + str(values)
            )
            print(
                "                    MSG: {0} -> {1}".format(
                    e.faultCode, "".join(e.faultString.split("\n")[-2:])
                )
            )
            return None

    # *************************************************************
    # Deletes  new element in odoo
    def odoo_delete(self, model_name, obj_ids):
        if self.xmlrpc_uid == None:
            self.getXMLRPCConnection()
        try:
            result = False
            if isinstance(obj_ids, list) or isinstance(obj_ids, tuple):
                result = self.xmlrpc_models.execute_kw(
                    self.context.getConfigValue("db_name"),
                    self.xmlrpc_uid,
                    self.context.getConfigValue("odoo_password"),
                    model_name,
                    "unlink",
                    [obj_ids],
                    {"context": self.odoo_context},
                )
            elif isinstance(obj_ids, int):
                result = self.xmlrpc_models.execute_kw(
                    self.context.getConfigValue("db_name"),
                    self.xmlrpc_uid,
                    self.context.getConfigValue("odoo_password"),
                    model_name,
                    "unlink",
                    [[obj_ids]],
                    {"context": self.odoo_context},
                )
            return result
        except xmlrpclib.Fault as e:
            print(
                "     WARNING: error when deleting object: "
                + model_name
                + " -> "
                + str(obj_ids)
            )
            print(
                "                    MSG: {0} -> {1}".format(
                    e.faultCode, "".join(e.faultString.split("\n")[-2:])
                )
            )
            return None

    # *************************************************************
    # Execute stuff in odoo   // Single Object
    def odoo_execute(self, model_name, method_name, obj_ids, parameters):
        if self.xmlrpc_uid == None:
            self.getXMLRPCConnection()
        try:
            result = False
            if isinstance(obj_ids, list) or isinstance(obj_ids, tuple):
                result = self.xmlrpc_models.execute_kw(
                    self.context.getConfigValue("db_name"),
                    self.xmlrpc_uid,
                    self.context.getConfigValue("odoo_password"),
                    model_name,
                    method_name,
                    [obj_ids, parameters],
                    {"context": self.odoo_context},
                )
            elif isinstance(obj_ids, int):
                result = self.xmlrpc_models.execute_kw(
                    self.context.getConfigValue("db_name"),
                    self.xmlrpc_uid,
                    self.context.getConfigValue("odoo_password"),
                    model_name,
                    method_name,
                    [[obj_ids], parameters],
                    {"context": self.odoo_context},
                )
            return result
        except xmlrpclib.Fault as e:
            print(
                "     WARNING: error when executing "
                + method_name
                + " on object: "
                + model_name
                + " -> "
                + str(parameters)
            )
            print(
                "                    MSG: {0} -> {1}".format(
                    e.faultCode, "".join(e.faultString.split("\n")[-2:])
                )
            )
            return None
