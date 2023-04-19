#!/usr/bin/env python3
"""
Simple OdooScript to updata Odoo translations
"""

import contextlib

from odoo import _, tools
from odoo.exceptions import UserError
from odootools import odooscript

try:
    from StringIO import StringIO  # for Python 2
except ImportError:
    from io import StringIO  # for Python 3


class UpdateTranslations(odooscript.AbstractOdooScript):
    """
    Updates all translations for a given odoo instance
    """

    def get_languages(self):
        """
        returns defined languages for instance
        """
        langs = self.env["res.lang"].search(
            [("active", "=", True), ("translatable", "=", True)]
        )
        return [(lang.code, lang.name, lang.id) for lang in langs]

    def get_lang_name(self, lang_code):
        """
        Get the full ref of install language
        """
        lang = self.env["res.lang"].search([("code", "=", lang_code)], limit=1)
        if not lang:
            raise UserError(_('No language with code "%s" exists') % lang_code)
        return lang.name

    # ***********************************
    # Main

    def run(self):
        """
        Do the processing, i.e. load translations
        """
        languages = self.get_languages()
        self.logger.warning(
            u"Will reload all following languages: %s", str(languages)
        )

        for lang_inst in languages:
            lang_code = lang_inst[0]
            lang_name = self.get_lang_name(lang_code)
            self.env["res.lang"].browse(lang_inst[2])

            # Synchronize
            with contextlib.closing(StringIO()) as buf:
                self.logger.warning(u"Synchronizing for : %s", lang_name)
                tools.trans_export(lang_code, ["all"], buf, "csv", self.cursor)
                tools.trans_load_data(
                    self.cursor, buf, "csv", lang_code, lang_name=lang_name
                )

            # Reload with override
            self.logger.warning(u"Reloading for : %s", lang_name)
            mods = self.env["ir.module.module"].search(
                [("state", "=", "installed")]
            )
            mods.with_context(overwrite=True).update_translations(lang_code)

        self.cursor.commit()


# *******************************************************
# Launch main function


if __name__ == "__main__":
    SCRIPT = UpdateTranslations()
    SCRIPT.run_in_odoo_context()
