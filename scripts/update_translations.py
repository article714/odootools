#!/usr/bin/env python
# -*- coding: utf-8 -*-

import contextlib
import cStringIO

from odoo import _, fields, models, tools
from odoo.exceptions import UserError
from odootools import OdooScript


class update_translations(OdooScript.Script):
    def get_languages(self):
        langs = self.env["res.lang"].search(
            [("active", "=", True), ("translatable", "=", True)]
        )
        return [(lang.code, lang.name, lang.id) for lang in langs]

    def get_lang_name(self, lang_code):
        lang = self.env["res.lang"].search([("code", "=", lang_code)], limit=1)
        if not lang:
            raise UserError(_('No language with code "%s" exists') % lang_code)
        return lang.name

    # ***********************************
    # Main

    def run(self):

        languages = self.get_languages()
        self.logger.warning(u"Will reload all following languages: %s", str(languages))

        for lang_inst in languages:
            lang_code = lang_inst[0]
            lang_name = self.get_lang_name(lang_code)
            lang = self.env["res.lang"].browse(lang_inst[2])

            # Synchronize
            with contextlib.closing(cStringIO.StringIO()) as buf:
                self.logger.warning(u"Synchronizing for : %s", lang_name)
                tools.trans_export(lang_code, ["all"], buf, "csv", self.cr)
                tools.trans_load_data(
                    self.cr, buf, "csv", lang_code, lang_name=lang_name
                )

            # Reload with override
            self.logger.warning(u"Reloading for : %s", lang_name)
            mods = self.env["ir.module.module"].search([("state", "=", "installed")])
            mods.with_context(overwrite=True).update_translations(lang_code)

        self.cr.commit()


# *******************************************************
# Launch main function


if __name__ == "__main__":
    script = update_translations()
    script.runInOdooContext()
