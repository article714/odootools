# -*- coding: utf-8 -*-

'''
Created on march 2018

Script used to unittest stuff

@author: C. Guychard
@copyright: ©2018 Article714
@license: AGPL
'''

import unittest

from odootools import OdooScript


@unittest.skip("Not a test class")
class TestScript(OdooScript.Script):
    '''
    A simple script used for unit testing
    '''

    def __init__(self):
        '''
        Constructor
        '''
        super(TestScript, self).__init__(parseConfig=False)
