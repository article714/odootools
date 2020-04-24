#!/usr/bin/env python3
"""
Simple OdooScript to remove an already installed Odoo module
"""


from odootools import odooscript


class RemoveModuleScript(  # pylint: disable=too-few-public-methods
    odooscript.AbstractOdooScript
):
    """
    See run()
    """

    # ***********************************
    # Main

    def run(self):
        """
        Removes a module (uninstall)
        """
        self.logger.info("Should Do something")
        # We need to write the code to remove a module !!!
        return 0


# *******************************************************
# Launch main function


if __name__ == "__main__":
    SCRIPT = RemoveModuleScript()
    SCRIPT.run()
