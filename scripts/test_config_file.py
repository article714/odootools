#!/usr/bin/env python
# -*- coding: utf-8 -*-


import OdooScript


class test_config_file(OdooScript.Script):
    def run(self):

        odoo_host = self.getConfigValue("odoo_host")
        url = "http://" + odoo_host + ":" + self.getConfigValue("odoo_port")
        db_name = self.getConfigValue("db_name")
        db_local = self.getConfigValue("db_local")

        print(
            "WILL USE ODOO SERVER : {}  \n \t AND DATABASE: {}   ({})".format(
                url, db_name, str(db_local)
            )
        )


# *******************************************************
# Launch main function
if __name__ == "__main__":
    script = test_config_file()
    script.run()
