#!/usr/bin/env python3
import logging
import sys
from os.path import isdir
from os.path import join as joinpath

import gevent.monkey

import odoo
import psycogreen.gevent
from odoo.cli.command import commands
from odoo.modules import get_module_path, get_modules

gevent.monkey.patch_all()

psycogreen.gevent.patch_psycopg()

if __name__ == "__main__":

    args = sys.argv[1:]

    # The only shared option is '--addons-path=' needed to discover additional
    # commands from modules
    if (
        len(args) > 1
        and args[0].startswith("--addons-path=")
        and not args[1].startswith("-")
    ):
        # parse only the addons-path, do not setup the logger...
        odoo.tools.config._parse_config([args[0]])
        args = args[1:]

    # Default legacy command
    command = "server"

    # TODO: find a way to properly discover addons subcommands without
    #        importing the world
    # Subcommand discovery
    if len(args) and not args[0].startswith("-"):
        logging.disable(logging.CRITICAL)
        for module in get_modules():
            if isdir(joinpath(get_module_path(module), "cli")):
                __import__("odoo.addons." + module)
        logging.disable(logging.NOTSET)
        command = args[0]
        args = args[1:]

    logging.warn("GAAAZOU: {}".format(str(commands)))

    logging.warn("MODULES: {}".format(str(get_modules())))
