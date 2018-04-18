# -*- coding: utf-8 -*-

'''
Created on march 2018

Test Utility functions to convert data


@author: C. Guychard
@copyright: ©2018 Article714
@license: AGPL
'''

from os import getcwd
from os.path import sep
import sys
import unittest

from .scripts.aTestScript import TestScript


class TestOdooScript(unittest.TestCase):

    def setUp(self):
        """Test Init"""
        sys.argv = ["testing", ]
        self.innerScript = TestScript()

    def test_parse_config(self):
        self.innerScript.parseConfig(
            aConfigfile='tests%setc%stestScript.config' % (sep, sep,))
        self.assertEquals(self.innerScript.getConfigValue(
            'language'), 'fr_FR', 'Unable to parse config')
