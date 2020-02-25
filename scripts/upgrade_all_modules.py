#!/usr/bin/env python
# -*- coding: utf-8 -*-

import odoo
from odoo.tools import config
from odootools import OdooScript


class upgrade_all_modules(OdooScript.Script):

    # ***********************************
    # Main

    def run(self):

        self.init_logs()

        self.odooargs = []
        if odoo is not False and self.config is not None:

            self.dbname = self.getConfigValue("db_name")
            db_host = self.getConfigValue("db_host")
            db_usr = self.getConfigValue("db_username")
            db_pwd = self.getConfigValue("db_password")

            if self.dbname is not None and odoo is not False:
                self.logger.info("CONNECTING TO DB : " + self.dbname)

            if odoo is not False and self.config is not None:
                self.odooargs.append("-c" + self.getConfigValue("odoo_config"))
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
                self.cr = registry.cursor()
                uid = odoo.SUPERUSER_ID
                ctx = odoo.api.Environment(self.cr, uid, {})["res.users"].context_get()
                self.env = odoo.api.Environment(self.cr, uid, ctx)

                self.logger.warn("FINISHING UPGRADE" + self.dbname)

                self.cr.commit()
                self.cr.close()

        else:
            self.logger.error("NO DB NAME given or No Odoo installation provided")


# *******************************************************
# Launch main function


if __name__ == "__main__":
    script = upgrade_all_modules()
    script.run()
