# -*- coding: utf-8 -*-

"""
Created on march 2018

Test Utility functions to convert data


@author: C. Guychard
@copyright: ©2018-2020 Article714
@license: AGPL
"""

from os.path import sep
import sys
import unittest

from .scripts.a_sample_script import SampleScript


class TestOdooScript(unittest.TestCase):
    """
    Test a sample script
    """

    def setUp(self):
        """Test Init"""
        super(TestOdooScript, self).setUp()
        sys.argv = ["testing"]
        self.inner_script = SampleScript()

    def test_parse_config(self):
        """
        Simply test parsing config file
        """
        self.inner_script.parse_config(
            aConfigfile=f"test{sep}setc{sep}testScript.config"
        )
        self.assertEqual(
            self.inner_script.get_config_value("language"),
            "fr_FR",
            "Unable to parse config",
        )
