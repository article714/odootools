# -*- coding: utf-8 -*-

"""
Created on march 2018

Script used to unittest stuff

@author: C. Guychard
@copyright: ©2018 Article714
@license: LGPL
"""

import pytest

from odootools import odooscript


@pytest.mark.skipif(True, reason="Not a test class")
class SampleScript(odooscript.AbstractOdooScript):
    """
    A simple script used for unit testing
    """

    def __init__(self):
        """
        Constructor
        """
        super(SampleScript, self).__init__(parse_config=False)

    def run(self):
        """
        I do run a test
        """

        self.logger.info("I'm running")
