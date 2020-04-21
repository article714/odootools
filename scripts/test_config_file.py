#!/usr/bin/env python

import odooscript


class TestConfigFile(odooscript.AbstractOdooScript):
    def run(self):

        odoo_host = self.get_config_value("odoo_host")
        url = "http://" + odoo_host + ":" + self.get_config_value("odoo_port")
        db_name = self.get_config_value("db_name")
        db_local = self.get_config_value("db_local")

        print(
            "WILL USE ODOO SERVER : {}  \n \t AND DATABASE: {}   ({})".format(
                url, db_name, str(db_local)
            )
        )


# *******************************************************
# Launch main function
if __name__ == "__main__":
    script = TestConfigFile()
    script.run()
