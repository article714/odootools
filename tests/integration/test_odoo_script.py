# -*- coding: utf-8 -*-

"""
Created on April 2023


@author: D. Couppé
@copyright: ©2023 Tekfor
@license: L-GPL
"""


from odootools.odooscript import AbstractOdooScript


class TestScript(AbstractOdooScript):
    AbstractOdooScript.getopt_options += "e:"
    AbstractOdooScript.getopt_long_options.extend(("extra=",))

    def run(self, cur, env):
        self.test_extra_param()
        self.test_odoo_env(env)

    def test_extra_param(self):
        extra_param = self.get_option("-e", "--extra")

        if extra_param != "test_extra_param":
            raise Exception(
                f"Extra parameter -e has not the correct value. Received : '{extra_param}' expected : 'test_extra_param'"
            )

    def test_odoo_env(self, env):
        name = env["res.users"].browse(1).name
        if name != "System":
            raise Exception(f"Expected : 'System', received : '{name}'")


if __name__ == "__main__":
    TEST_SCRIPT = TestScript()
    TEST_SCRIPT.run_in_odoo_context()
