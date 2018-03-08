# -*- coding: utf-8 -*-

'''
Created on march 2018

Utility functions to convert data


@author: C. Guychard
@copyright: ©2018 Article714
@license: AGPL
'''

import logging
import sys
import xmlrpclib

from .StringConverters import toString


try:
    import pgdb
except:
    pgdb = False
    logging.error("error on import PGDB module")


class Connection:

    # scripting context
    context = None

    # xmlrpc connection
    xmlrpc_uid = None
    xmlrpc_models = None

    # db connection
    db_con = None

    # *************************************************************
    # constructor
    # parameter script must be an instance of OdooScript
    def __init__(self, script):
        self.context = script

    # *************************************************************
    # gets a New XMLRPC connection to odoo
    def getXMLRPCConnection(self):

        if (self.xmlrpc_uid != None):
            return (self.xmlrpc_uid, self.xmlrpc_models)

        odoo_host = self.context.getConfigValue('odoo_host')
        odoo_port = self.context.getConfigValue('odoo_port')
        if odoo_port == '443':
            url = 'https://' + odoo_host
        else:
            url = 'http://' + odoo_host + ':' + self.context.getConfigValue('odoo_port')
        odoo_username = self.context.getConfigValue('odoo_username')

        # *************************************************************
        # establish xmlrpc link
        # http://www.odoo.com/documentation/9.0/api_integration.html

        common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))

        self.odoo_context = {'lang':self.context.getConfigValue('language')}

        uid = common.authenticate(self.context.getConfigValue('db_name'),
                                  self.context.getConfigValue('odoo_username'),
                                  self.context.getConfigValue('odoo_password'), self.odoo_context)

        odoo_models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url), allow_none=1, verbose=0)

        if not uid:
            print ("ERROR: Not able to connect to Odoo with given information, username: " + odoo_username)
            sys.exit(1)

        self.xmlrpc_uid = uid
        self.xmlrpc_models = odoo_models

        return (uid, odoo_models)

    # *************************************************************
    # gets a New Postgresql connection to odoo
    def getDBConnection(self):
        db_name = self.context.getConfigValue('db_name')

        if pgdb:
            # *************************************************************
            # connect to Db
            ldsn = self.context.getConfigValue('db_host') + ":5432"
            if (self.context.getConfigValue('db_local') == "1"):
                return pgdb.connect(database=db_name,
                              user=self.context.getConfigValue('db_username'))
            else:
                if self.context.getConfigValue('db_password') != None:
                    return pgdb.connect(database=db_name, dsn=ldsn,
                              user=self.context.getConfigValue('db_username'),
                              password=self.context.getConfigValue('db_password'))
                else:
                    return pgdb.connect(database=db_name, dsn=ldsn,
                              user=self.context.getConfigValue('db_username'))
        else:
            logging.error("No PGDB module")



    #********************************************************************************
    # helper function to search and create or write if exist

    def odoo_search_create_or_write (self, model_name, search_criteria=[], values={}, create_only=False, can_be_archived=False):
        ALL_INSTANCES_FILTER = (u'|', (u'active', u'=', True), (u'active', u'!=', True))
      
        if (self.xmlrpc_uid == None):
            self.getXMLRPCConnection()
        try:
            if can_be_archived:
                full_search = copy.copy(search_criteria)
                for val in ALL_INSTANCES_FILTER:
                    full_search.append(val)
                found = self.xmlrpc_models.execute_kw(self.context.getConfigValue('db_name'),
                                                   self.xmlrpc_uid,
                                                   self.context.getConfigValue('odoo_password'),
                                                    model_name, 'search_read', [full_search], 0, 0, False, False, self.odoo_context)
            else:
                found = self.xmlrpc_models.execute_kw(self.context.getConfigValue('db_name'),
                                                   self.xmlrpc_uid,
                                                   self.context.getConfigValue('odoo_password'),
                                                    model_name, 'search_read', [search_criteria], 0, 0, False, False, self.odoo_context)
                
                
            lfound = len(found)
            # create only if do not exist
            if lfound == 0:
                try:
                    result = self.xmlrpc_models.execute_kw(self.context.getConfigValue('db_name'),
                                                   self.xmlrpc_uid,
                                                   self.context.getConfigValue('odoo_password'),
                                                    model_name, 'create', values)
                except Exception as e:
                    self.logger.error("Failed to create record " + model_name + " [ " + toString(values) + "] " + toString(e))

            elif lfound == 1:
                odoobject = found[0]
                try:
                    if not create_only:
                        odoobject.write(values)
                except Exception as e:
                    self.logger.error("Echec de mise à jour d'un enregistrement " + model._name + "(" + toString(odoobject.id) + ") [ " + toString(values) + "] " + toString(e))
            else:
                self.logger.warning("Echec de la mise à jour d'un enregistrement (" + model._name + ") trop d'objets trouvés pour " + str(search_criteria))

            self.cr.commit()

            return odoobject

        except Exception as e:
            self.logger.error("WARNING Error when looking for or writing a record for model: " + model._name + " [ " + toString(values) + "] " + toString(e))
            
    # *************************************************************
    # Search elements in odoo
    def odoo_search(self, model_name, search_conditions, result_parameters):
        if (self.xmlrpc_uid == None):
            self.getXMLRPCConnection()
        try:
            result = self.xmlrpc_models.execute_kw(self.context.getConfigValue('db_name'),
                                                   self.xmlrpc_uid,
                                                   self.context.getConfigValue('odoo_password'),
                                                    model_name, 'search_read', [search_conditions], result_parameters)
            return result
        except xmlrpclib.Fault as e:
            logging.exception("WARNING: error when searching for object: " + model_name + " -> " + str(search_conditions))
            return ()

    # *************************************************************
    # Search id of elements in odoo with language support enabled
    def odoo_search_l10n(self, model_name, search_conditions, fields_selection):
        if (self.xmlrpc_uid == None):
            self.getXMLRPCConnection()
        try:
            result = self.xmlrpc_models.execute(self.context.getConfigValue('db_name'),
                                                   self.xmlrpc_uid,
                                                   self.context.getConfigValue('odoo_password'),
                                                    model_name, 'search_read', search_conditions, fields_selection, 0, 0, False, self.odoo_context)
            return result
        except xmlrpclib.Fault as e:
            logging.exception("     WARNING: error when searching for object: " + model_name + " -> " + str(search_conditions))
            return ()

    # *************************************************************
    # Search id of elements in odoo with language support enabled
    def odoo_idsearch(self, model_name, search_conditions):
        if (self.xmlrpc_uid == None):
            self.getXMLRPCConnection()
        try:
            result = self.xmlrpc_models.execute(self.context.getConfigValue('db_name'),
                                                   self.xmlrpc_uid,
                                                   self.context.getConfigValue('odoo_password'),
                                                    model_name, 'search', search_conditions, 0, 0, False, False, self.odoo_context)
            return result
        except xmlrpclib.Fault as e:
            logging.exception("     WARNING: error when searching for object: " + model_name + " -> " + str(search_conditions))
            return ()

    # *************************************************************
    # Read elements in odoo
    def odoo_read(self, model_name, ids):
        if (self.xmlrpc_uid == None):
            self.getXMLRPCConnection()

        try:
            result = self.xmlrpc_models.execute_kw(self.context.getConfigValue('db_name'),
                                                   self.xmlrpc_uid,
                                                   self.context.getConfigValue('odoo_password'),
                                                    model_name, 'read', [ids])
            return result

        except xmlrpclib.Fault as e:
            print ("     WARNING: error when reading  object: " + model_name + " -> " + str(ids))
            print ("                    MSG: {0} -> {1}".format(e.faultCode, ''.join(e.faultString.split('\n')[-2:])))
            return None

    # *************************************************************
    # Update element in odoo   // Single Object
    def odoo_write(self, model_name, obj_id, values):
        if (self.xmlrpc_uid == None):
            self.getXMLRPCConnection()
        try:
            result = self.xmlrpc_models.execute_kw(self.context.getConfigValue('db_name'),
                                                   self.xmlrpc_uid,
                                                   self.context.getConfigValue('odoo_password'),
                                                    model_name, 'write', [obj_id, values])
            return result
        except xmlrpclib.Fault as e:
            print ("     WARNING: error when writing object: " + model_name + " -> " + str(values))
            print ("                    MSG: {0} -> {1}".format(e.faultCode, ''.join(e.faultString.split('\n')[-2:])))
            return None

    # *************************************************************
    # Create  new element in odoo   // Single Object
    def odoo_create(self, model_name, *values):
        if (self.xmlrpc_uid == None):
            self.getXMLRPCConnection()
        try:
            result = self.xmlrpc_models.execute_kw(self.context.getConfigValue('db_name'),
                                                   self.xmlrpc_uid,
                                                   self.context.getConfigValue('odoo_password'),
                                                    model_name, 'create', values)
            return result
        except xmlrpclib.Fault as e:
            print ("     WARNING: error when creating object: " + model_name + " -> " + str(values))
            print ("                    MSG: {0} -> {1}".format(e.faultCode, ''.join(e.faultString.split('\n')[-2:])))
            return None

    # *************************************************************
    # Execute stuff in odoo   // Single Object
    def odoo_execute(self, model_name, method_name, obj_id, parameters):
        if (self.xmlrpc_uid == None):
            self.getXMLRPCConnection()
        try:
            result = self.xmlrpc_models.execute_kw(self.context.getConfigValue('db_name'),
                                                   self.xmlrpc_uid,
                                                   self.context.getConfigValue('odoo_password'),
                                                    model_name, method_name, [obj_id], parameters)
            return result
        except xmlrpclib.Fault as e:
            print ("     WARNING: error when executing " + method_name + " on object: " + model_name + " -> " + str(parameters))
            print ("                    MSG: {0} -> {1}".format(e.faultCode, ''.join(e.faultString.split('\n')[-2:])))
            return None

