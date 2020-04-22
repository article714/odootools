"""
Experimental Do Nothing :'()
"""


class OdooTestCommand:
    """
    Attempt to write an Odoo Command
    """

    def __init__(self):
        super(OdooTestCommand, self).__init__()
        self.value = 17

    def will_do(self):
        """
        One Day
        """
        return 17 + self

    def someting(self):
        """
        One Day
        """
        return 17 + self
