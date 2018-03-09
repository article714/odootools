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
from tests.aTestScript import TestScript


class TestOdooConn(unittest.TestCase):
    
    def setUp(self):
        """Test Init"""
        sys.argv = ["testing", ]
        self.innerScript = TestScript()
        self.innerScript.parseConfig(aConfigfile='tests%setc%stestScript.config' % (sep, sep,))

    def test_conn(self):
         
        self.odooConn = OdooConnection.Connection(self.innerScript)
        self.assertIsNotNone(self.odooConn, "Failed to create connection object")
        self.odooxmlrpc = self.odooConn.getXMLRPCConnection()
        self.assertIsNotNone(self.odooxmlrpc, "Failed to init connection")

