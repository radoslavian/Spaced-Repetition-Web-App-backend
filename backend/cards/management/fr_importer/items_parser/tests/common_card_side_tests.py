class CommonCardSideTests:
    """
    Tests common to both sides of a card. The actual case must inherit
    from the 'TestCase' class.
    """
    def assert_no_illegal_formatting_tags(self, card_field):
        self.assertNotIn("<b>", card_field)
        self.assertNotIn("</b>", card_field)
        self.assertNotIn("<u>", card_field)
        self.assertNotIn("</u>", card_field)

    def assert_allowed_tags(self, card_field):
        self.assertRegex(card_field,
                         "r<strike>|</strike>")
        self.assertRegex(card_field,
                         "r<i>|</i>")
