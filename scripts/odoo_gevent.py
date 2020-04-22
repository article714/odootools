#!/usr/bin/env python3

"""
Running a Gevent-ed ODoo
"""

import logging
import sys
from os.path import isdir
from os.path import join as joinpath

import gevent.monkey
import psycogreen.gevent

import odoo
from odoo.modules import get_module_path, get_modules

gevent.monkey.patch_all()

psycogreen.gevent.patch_psycopg()

if __name__ == "__main__":

    ARGS = sys.argv[1:]

    # The only shared option is '--addons-path=' needed to discover additional
    # commands from modules
    if (
        len(ARGS) > 1
        and ARGS[0].startswith("--addons-path=")
        and not ARGS[1].startswith("-")
    ):
        # parse only the addons-path, do not setup the logger...
        odoo.tools.config._parse_config(  # pylint: disable=protected-access
            [ARGS[0]]
        )
        ARGS = ARGS[1:]

    # Default legacy command
    COMMAND = "server"

    # Subcommand discovery
    if ARGS and not ARGS[0].startswith("-"):
        logging.disable(logging.CRITICAL)
        for module in get_modules():
            if isdir(joinpath(get_module_path(module), "cli")):
                __import__("odoo.addons." + module)
        logging.disable(logging.NOTSET)
        COMMAND = ARGS[0]
        ARGS = ARGS[1:]

    logging.warning("GAAAZOU: %s", str(COMMAND))

    logging.warning("MODULES: %s", str(get_modules()))
