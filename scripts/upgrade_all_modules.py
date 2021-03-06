#!/usr/bin/env python3
"""
Simple OdooScript to upgrade all installed modules
"""

import odoo
from odoo.tools import config
from odootools import odooscript


class UpgradeAllModules(odooscript.AbstractOdooScript):
    """
    See run()
    """

    def __init__(self):
        super(UpgradeAllModules, self).__init__()

        self.odooargs = []
        self.env = None
        self.cursor = None
        self.dbname = None

    def run(self):
        """
        Simple OdooScript to upgrade all installed modules
        """

        self.init_logs()

        # Do we still need this?
        if self.config is not None:

            self.dbname = self.get_config_value("db_name")
            db_host = self.get_config_value("db_host")
            db_usr = self.get_config_value("db_username")
            db_pwd = self.get_config_value("db_password")

            if self.dbname is not None and odoo is not False:
                self.logger.info("CONNECTING TO DB : %s ", self.dbname)

            if odoo is not False and self.config is not None:
                self.odooargs.append(
                    "-c" + self.get_config_value("odoo_config")
                )
                self.odooargs.append("-d" + self.dbname)
                if db_host:
                    self.odooargs.append("--db_host=%s" % db_host)
                if db_usr and db_pwd:
                    self.odooargs.append("-r%s" % db_usr)
                    self.odooargs.append("-w%s" % db_pwd)
                self.odooargs.append("--update=all")

            config.parse_config(self.odooargs)

            odoo.cli.server.report_configuration()

            with odoo.api.Environment.manage():
                registry = odoo.registry(self.dbname)
                odoo.modules.load_modules(registry)
                self.cursor = registry.cursor()
                uid = odoo.SUPERUSER_ID
                ctx = odoo.api.Environment(self.cursor, uid, {})[
                    "res.users"
                ].context_get()
                self.env = odoo.api.Environment(self.cursor, uid, ctx)

                # We need to check that this works!!!

                self.logger.warning("FINISHING UPGRADE %s", self.dbname)

                self.cursor.commit()
                self.cursor.close()

        else:
            self.logger.error(
                "NO DB NAME given or No Odoo installation provided"
            )


# *******************************************************
# Launch main function


if __name__ == "__main__":
    SCRIPT = UpgradeAllModules()
    SCRIPT.run()
