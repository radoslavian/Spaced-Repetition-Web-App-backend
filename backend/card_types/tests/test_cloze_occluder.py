from unittest import TestCase as UnitTestCase

from card_types.card_managers.cloze_occluder import ClozeOccluder, \
    FormattedClozeOccluder


class ClozeOccluding(UnitTestCase):
    """
    Case for the helper class occluding gaps in the card description text.
    """
    @classmethod
    def setUpClass(cls):
        cls.cloze_id_one = "one"
        cls.cloze_id_two = "two"
        cls.cloze_id_three = "three"
        cls.text = (f'<cloze id="{cls.cloze_id_one}">cloze one</cloze> '
                    f'<cloze id="{cls.cloze_id_two}">cloze two</cloze> '
                    f'<cloze id="{cls.cloze_id_three}">cloze three</cloze>')
        cloze_occluder = ClozeOccluder(cls.text)
        cls.received_output = cloze_occluder.get_cards()

    def test_occluding_clozes(self):
        expected_output = [
            {
                "cloze-id": self.cloze_id_one,
                "front": '[...] {...} {...}',
                "back": '[cloze one] cloze two cloze three'
            },
            {
                "cloze-id": self.cloze_id_two,
                "front": '{...} [...] {...}',
                "back": 'cloze one [cloze two] cloze three'
            },
            {
                "cloze-id": self.cloze_id_three,
                "front": '{...} {...} [...]',
                "back": 'cloze one cloze two [cloze three]'
            }
        ]
        self.assertListEqual(self.received_output, expected_output)


class FormattedClozeOccluding(UnitTestCase):
    @classmethod
    def setUpClass(cls):
        cls.id_one = "one"
        cls.id_two = "cloze two"
        cls.text = (f'<cloze id="{cls.id_one}">cloze one</cloze> '
                    f'<cloze id="{cls.id_two}">cloze two</cloze>')

    def setUp(self):
        self.formatted_occluder = FormattedClozeOccluder(self.text)

    def test_occluder(self):
        expected_output = {
                "cloze-id": self.id_one,
                "front": '<span class="highlighted-text">[&hellip;]'
                                 '</span> '
                                 '<span class="toned-down-text">[&hellip;]'
                                 '</span>',
                "back": '<span class="highlighted-text">[cloze one]'
                               '</span> cloze two'
            }
        received_output = self.formatted_occluder.get_cards()[0]
        self.assertEqual(expected_output, received_output)
