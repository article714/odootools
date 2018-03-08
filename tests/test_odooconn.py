# -*- coding: utf-8 -*-

'''
Created on march 2018

Utility functions to convert data


@author: C. Guychard
@copyright: ©2018 Article714
@license: AGPL
'''

import unittest
from odootools import OdooConnection


class TestStringMethods(unittest.TestCase):
    """
    TODO TODO TODO
    """

    def test_conn(self):
         
        self.odooConn = OdooConnection.Connection(self)
        self.odooxmlrpc = self.odooConn.getXMLRPCConnection()

        self.assertTrue('BONJOUR'.isupper())
        self.assertFalse('BONJOUddR'.isupper())

if __name__ == '__main__':
    unittest.main()