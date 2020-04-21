# -*- coding: utf-8 -*-

"""
Created on march 2018

Utility functions to convert data


@author: C. Guychard
@copyright: ©2018-2020 Article714
@license: AGPL
"""

from datetime import date, datetime

from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
)

from .StringConverters import toString

# -------------------------------------------------------------------------------------
# CONSTANTS
XLS_DATE_REF = date(1900, 1, 1)


# -------------------------------------------------------------------------------------
#  Utility: Transfo de chaine en date


def dateToOdooString(val):
    if isinstance(val, datetime):
        return val.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    elif isinstance(val, date):
        return val.strftime(DEFAULT_SERVER_DATE_FORMAT)
    else:
        return toString(val)
