# -*- coding: utf-8 -*-

"""
Created on march 2018

Test Utility functions to convert data


@author: C. Guychard
@copyright: ©2018 Article714
@license: AGPL
"""

from os import getcwd
from os.path import sep
import sys
import unittest

from test.scripts.aSampleScript import SampleScript


class TestOdooScript(unittest.TestCase):
    def setUp(self):
        """Test Init"""
        sys.argv = ["testing"]
        self.innerScript = SampleScript()

    def test_parse_config(self):
        self.innerScript.parse_config(
            aConfigfile="test%setc%stestScript.config" % (sep, sep)
        )
        self.assertEquals(
            self.innerScript.get_config_value("language"),
            "fr_FR",
            "Unable to parse config",
        )
