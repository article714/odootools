# -*- coding: utf-8 -*-

"""

Module to manipulate data in Odoo via XML-RPC or embedded in a script

@author: C. Guychard
@copyright: ©2017-2020 Article714
@license: AGPL
"""

import logging
from sys import exit

try:
    from . import Converters
    from . import OdooConnection
    from . import OdooScript
except (ModuleNotFoundError, ImportError):
    logging.error("error on Odoo import")
    exit(1)
