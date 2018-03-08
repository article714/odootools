# -*- coding: utf-8 -*-

'''
Created on march 2018

Utility functions to convert data


@author: C. Guychard
@copyright: ©2018 Article714
@license: AGPL
'''

from datetime import date, timedelta, datetime

#-------------------------------------------------------------------------------------
# CONSTANTS

XLS_DATE_REF = date(1900, 1, 1)


#-------------------------------------------------------------------------------------
#  Utility: Transfo des chaines en unicode
def toString(value):
    avalue = ""
    if isinstance(value, str):
        try:
            avalue = unicode(value)
        except UnicodeError:
            avalue = unicode(value.decode('iso-8859-1'))
    elif isinstance(value, unicode):
        avalue = value
    elif isinstance(value, Exception):
        avalue = str(type(value)) + " -- " + str(value)
    elif isinstance(value, object):
        avalue = str(value)
    else:
        try:
            avalue = unicode("" + str(value))
        except UnicodeDecodeError:
            avalue = unicode(value.decode('iso-8859-1'))
    return avalue

#-------------------------------------------------------------------------------------
#  Utility: Transfo de chaine en date


def toDate(value):

    val_date = None

    try:
        val = float(value)
        val_date = XLS_DATE_REF + timedelta(val)
    except Exception:
        val_date = None

    if val_date == None:
        try:
            val_date = datetime.strptime(value, '%d/%m/%Y')
        except Exception:
            val_date = None
        try:
            if val_date == None:
                val_date = datetime.strptime(value, '%Y-%m-%d 00:00:00')
        except Exception:
            val_date = None

    return val_date



#-------------------------------------------------------------------------------------
#  Utility: Transfo de valeur en float
def toFloat(value):

    try:
        val = float(value)
    except Exception:
        val = None

    return val


#-------------------------------------------------------------------------------------
# translate string to Int
# None, unparseable or empty string is -1
def toInt(s):
    try:
        if s != None:
            if len(s) == 0:
                return -1
            else:
                return int(s)
        else:
            return -1
    except ValueError:
        try:
            return int(float(s))
        except ValueError:
            return -1

