# -*- coding: utf-8 -*-

"""
Created on march 2018

Utility functions to convert data


@author: C. Guychard
@copyright: ©2018 Article714
@license: LGPL
"""
from os.path import sep
import sys
import unittest

from odootools import odooconnection
from ..scripts.a_sample_script import SampleScript


class TestOdooConn(unittest.TestCase):
    """
    Odoo Connection Test
    """

    def setUp(self):
        """Test Init"""
        super(TestOdooConn, self).setUp()
        self.odooxmlrpc = None
        import os

        sys.argv = ["testing"]
        self.inner_script = SampleScript()
        self.inner_script.parse_config(
            configfile="tests%setc%stestScript.config" % (sep, sep)
        )

        self.connection = odooconnection.Connection(self.inner_script)

    def test_conn(self):
        """
        Test the Connection
        """
        self.assertIsNotNone(self.connection, "Failed to create connection object")
        self.odooxmlrpc = self.connection.get_odoo_xmlrpc_connection()
        self.assertIsNotNone(self.odooxmlrpc, "Failed to init connection")

    def test_odoo_search(self):
        """
        Test the search
        """
        self.assertIsNotNone(self.connection, "Failed to create connection object")
        found = self.connection.odoo_idsearch(
            "res.partner", [("is_company", "=", True)]
        )
        self.assertIsNotNone(found)
        self.assertGreater(len(found), 0, "No partner found, issue!")

    def test_odoo_search_create_or_write(self):
        """
        Test the creation of a record
        """
        self.assertIsNotNone(self.connection, "Failed to create connection object")
        found = self.connection.odoo_search_create_or_write(
            "res.partner",
            [("name", "=", "Someone who cares")],
            values={"name": "Someone who cares", "street": "Anywhere"},
        )
        self.assertIsNotNone(found, "No partner found, issue!")
        self.assertGreater(found, 0, "No partner found, issue!")
        found = self.connection.odoo_search_create_or_write(
            "res.partner",
            [("name", "=", "Someone who cares")],
            values={"name": "Someone who cares", "street": "Anywhere"},
        )
        self.assertIsNotNone(found, "No partner found, issue!")
        self.assertGreater(found, 0, "No partner found, issue!")

    def test_odoo_search_delete(self):
        """
        Test the search & deletion of a record
        """
        self.assertIsNotNone(self.connection, "Failed to create connection object")
        found = self.connection.odoo_idsearch(
            "res.partner", [("name", "=", "Someone who cares")]
        )
        self.assertIsNotNone(found, "No partner found, issue!")
        self.assertGreater(len(found), 0, "No partner found, issue!")
        for anid in found:
            self.connection.odoo_delete("res.partner", anid)
        found = self.connection.odoo_idsearch(
            "res.partner", [("name", "=", "Someone who cares")]
        )
        self.assertEqual(len(found), 0, "Ppartner found, issue!")
