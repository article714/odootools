# -*- coding: utf-8 -*-

"""

Module to manipulate data in Odoo via XML-RPC or embedded in a script

@author: C. Guychard
@copyright: ©2017 Article714
@license: AGPL
"""

import logging
from . import StringConverters

try:
    from . import Converters
    from . import OdooConnection
    from . import OdooScript
except:
    logging.error("error on Odoo import")
    exit
