# -*- coding: utf-8 -*-

"""
Created on march 2018

Utility functions to convert data


@author: C. Guychard
@copyright: ©2018-2020 Article714
@license: AGPL
"""

from datetime import date, timedelta, datetime

# -------------------------------------------------------------------------------------
# CONSTANTS

XLS_DATE_REF = date(1900, 1, 1)


# -------------------------------------------------------------------------------------
def to_string(value):
    """
    Utility: Transfo des chaines en unicode
    """
    avalue = ""
    if isinstance(value, str):
        avalue = value
    elif isinstance(value, Exception):
        avalue = str(type(value)) + " -- " + str(value)
    elif isinstance(value, object):
        avalue = str(value)
    else:
        avalue = str(value)
    return avalue


# -------------------------------------------------------------------------------------
def to_date(value):
    """
    Utility: Transfo de chaine en date
    """
    val_date = None

    try:
        val = float(value)
        val_date = XLS_DATE_REF + timedelta(val)
    except Exception:
        val_date = None

    if val_date is None:
        try:
            val_date = datetime.strptime(value, "%d/%m/%Y")
        except Exception:
            val_date = None
        try:
            if val_date is None:
                val_date = datetime.strptime(value, "%Y-%m-%d 00:00:00")
        except Exception:
            val_date = None

    return val_date


# -------------------------------------------------------------------------------------
def to_float(value):
    """"
    Utility: Transfo de valeur en float
    """"
    try:
        val = float(value)
    except ValueError:
        val = None

    return val


# -------------------------------------------------------------------------------------
def to_int(strval):
    """
    translate string to Int
        None, unparseable or empty string is -1
    """
    try:
        if strval is not None:
            if not strval:
                return -1
            return int(strval)
        return -1
    except ValueError:
        try:
            return int(float(strval))
        except ValueError:
            return -1
