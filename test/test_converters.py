# -*- coding: utf-8 -*-

'''
Created on march 2018

Test Utility functions to convert data


@author: C. Guychard
@copyright: ©2018 Article714
@license: AGPL
'''

from datetime import datetime
import unittest

from odootools import StringConverters


class TestConverters(unittest.TestCase):
    
    def setUp(self):
        """Test Init"""
        self.aDate = datetime.now()

    def test_date_to_string(self):
        val = StringConverters.toString(self.aDate)
        self.assertIsNotNone(val, "unable to translate date")