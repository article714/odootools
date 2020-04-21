# -*- coding: utf-8 -*-

"""
Created on march 2018

Script used to unittest stuff

@author: C. Guychard
@copyright: ©2018 Article714
@license: AGPL
"""

import pytest

from odootools import odooscript


@pytest.mark.skipif(True, reason="Not a test class")
class SampleScript(odooscript.Script):
    """
    A simple script used for unit testing
    """

    def __init__(self):
        """
        Constructor
        """
        super(SampleScript, self).__init__(parse_config=False)
