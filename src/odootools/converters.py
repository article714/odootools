# -*- coding: utf-8 -*-

"""
Created on march 2018

Utility functions to convert data


@author: C. Guychard
@copyright: ©2018-2020 Article714
@license: LGPL
"""

from datetime import date, datetime

from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
)

from .stringconverters import to_string

# -------------------------------------------------------------------------------------
# CONSTANTS
XLS_DATE_REF = date(1900, 1, 1)


# -------------------------------------------------------------------------------------
def date_to_odoo_string(val):
    """ "
    Utility: translate date to an Odoo compatible string
    """
    if isinstance(val, datetime):
        return val.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    if isinstance(val, date):
        return val.strftime(DEFAULT_SERVER_DATE_FORMAT)
    return to_string(val)
