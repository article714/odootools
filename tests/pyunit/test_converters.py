# -*- coding: utf-8 -*-

"""
Created on march 2018

Test Utility functions to convert data


@author: C. Guychard
@copyright: ©2018-2020 Article714
@license: LGPL
"""

from datetime import datetime
import unittest

from odootools import stringconverters


class TestConverters(unittest.TestCase):
    """
    Test String converters
    """

    def setUp(self):
        """Test Init"""
        super(TestConverters, self).setUp()
        self.a_date = datetime.now()

    def test_date_to_string(self):
        """Test Date formatting to String"""
        val = stringconverters.to_string(self.a_date)
        self.assertIsNotNone(val, "unable to translate date")
