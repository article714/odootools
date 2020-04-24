# -*- coding: utf-8 -*-

"""

Module to manipulate data in Odoo via XML-RPC or embedded in a script

@author: C. Guychard
@copyright: ©2017-2020 Article714
@license: AGPL
"""

import logging
from sys import exit as sysexit

try:
    from . import converters
    from . import odooconnection
    from . import odooscript
except ImportError:
    logging.exception("error on Odoo import")
    sysexit(1)
