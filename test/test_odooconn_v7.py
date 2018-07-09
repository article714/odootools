# -*- coding: utf-8 -*-

'''
Created on march 2018

Utility functions to convert data


@author: C. Guychard
@copyright: ©2018 Article714
@license: AGPL
'''

from os.path import sep
import sys
import unittest

from odootools import OdooConnection
from test.scripts.aSampleScript import SampleScript


class TestOdooConn(unittest.TestCase):

    def setUp(self):
        """Test Init"""
        sys.argv = ["testing", ]
        self.innerScript = SampleScript()
        self.innerScript.parseConfig(
            aConfigfile='test%setc%stestScriptV7.config' % (sep, sep,))

        self.odooConn = OdooConnection.Connection(self.innerScript)

    def test_conn(self):
        self.assertIsNotNone(
            self.odooConn, "Failed to create connection object")
        self.odooxmlrpc = self.odooConn.getXMLRPCConnection()
        self.assertIsNotNone(self.odooxmlrpc, "Failed to init connection")

    def test_odoo_search(self):
        self.assertIsNotNone(
            self.odooConn, "Failed to create connection object")
        found = self.odooConn.odoo_idsearch(
            'res.partner', [('is_company', '=', True)])

        self.assertGreater(len(found), 0, "No partner found, issue!")

    def test_odoo_search_create_or_write(self):
        self.assertIsNotNone(
            self.odooConn, "Failed to create connection object")
        found = self.odooConn.odoo_search_create_or_write('res.partner', [(
            'name', '=', 'Someone who cares')], values={'name': 'Someone who cares', 'street': 'Anywhere'})
        self.assertIsNotNone(found, 'No partner found, issue!')
        self.assertGreater(found, 0, "No partner found, issue!")
        found = self.odooConn.odoo_search_create_or_write('res.partner', [(
            'name', '=', 'Someone who cares')], values={'name': 'Someone who cares', 'street': 'Anywhere'})
        self.assertIsNotNone(found, 'No partner found, issue!')
        self.assertGreater(found, 0, "No partner found, issue!")

    def test_odoo_search_delete(self):
        self.assertIsNotNone(
            self.odooConn, "Failed to create connection object")
        found = self.odooConn.odoo_idsearch(
            'res.partner', [('name', '=', 'Someone who cares')])
        self.assertIsNotNone(found, 'No partner found, issue!')
        self.assertGreater(len(found), 0, "No partner found, issue!")
        for id in found:
            self.odooConn.odoo_delete('res.partner', id)
        found = self.odooConn.odoo_idsearch(
            'res.partner', [('name', '=', 'Someone who cares')])
        self.assertEqual(len(found), 0, "Ppartner found, issue!")
