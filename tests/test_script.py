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

TRAVIS_TEST = "Yes"


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
            configfile="tests{asep}etc{asep}testScript.config".format(asep=sep)
        )

        self.assertEqual(
            self.inner_script.get_config_value("language"),
            "fr_FR",
            "Unable to parse config",
        )

    def test_parse_config_sections(self):
        """
        Simply test parsing config file with sections
        """
        self.inner_script.parse_config(
            configfile="tests{asep}etc{asep}testSections.config".format(
                asep=sep
            )
        )
        self.assertEqual(
            self.inner_script.get_config_value("language", section="GENERAL"),
            "fr_FR",
            "Unable to parse config",
        )
        self.assertEqual(
            self.inner_script.get_config_value("testing"),
            "true",
            "Unable to parse config",
        )

        self.assertEqual(
            self.inner_script.get_config_value("testing", datatype="bool"),
            True,
            "Unable to parse config",
        )
