#!/usr/bin/env python3
"""
Simple OdooScript to verify a provided config file
"""

from odootools import odooscript


class TestConfigFile(odooscript.AbstractOdooScript):
    """
    Verifies that provided config file is correct
    """

    def run(self):
        """
        main processing
        """
        odoo_host = self.get_config_value("odoo_host")
        url = "http://" + odoo_host + ":" + self.get_config_value("odoo_port")
        db_name = self.get_config_value("db_name")
        db_local = self.get_config_value("db_local")

        self.logger.warning(
            "WILL USE ODOO SERVER : %s  \n \t AND DATABASE: %s   (%s)",
            url,
            db_name,
            str(db_local),
        )


# *******************************************************
# Launch main function
if __name__ == "__main__":
    SCRIPT = TestConfigFile()
    SCRIPT.run()
