from unittest import skip, TestCase as UnittestTestCase
from django.test import TestCase

from card_types.card_managers.cloze_occluder import ClozeOccluder, \
    FormattedClozeOccluder
from card_types.models import CardNote


class ClozeOccluding(UnittestTestCase):
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


class FormattedClozeOccluding(UnittestTestCase):
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


@skip
class GeneratingCorrectCards(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cloze_id_one = "one"
        cls.cloze_id_two = "two"
        cls.cloze_id_three = "three"
        cls.text = (f'<cloze id="{cls.cloze_id_one}">cloze one</cloze> '
                    f'<cloze id="{cls.cloze_id_two}">cloze two</cloze> '
                    f'<cloze id="{cls.cloze_id_three}">cloze three</cloze>')
        card_description = {
            "text": cls.text
        }
        card_type = "occluded-cloze-deletion"
        cls.note = CardNote.objects.create(card_description=card_description,
                                           card_type=card_type)
        cls._get_cards_from_note_metadata()

    @classmethod
    def _get_cards_from_note_metadata(cls):
        """
        Fetches cards from note metadata.
        For this reason, though not a test itself, it is important for metadata
        testing.
        """
        cls.cloze_one_card_details = [
            card for card in
            cls.note.metadata["managed-cards-mapping"]
            if card["cloze-id"] == cls.cloze_id_one]
        cls.cloze_two_card_details = [card for card in
                                      cls.note.metadata[
                                          "managed-cards-mapping"]
                                      if card["cloze-id"] == cls.cloze_id_two]
        cloze_one_card_id = cls.cloze_one_card_details[0]["card-id"]
        cls.cloze_one_card = cls.note.cards.get(id=cloze_one_card_id)
        cloze_two_card_id = cls.cloze_two_card_details[0]["card-id"]
        cls.cloze_two_card = cls.note.cards.get(id=cloze_two_card_id)

    def test_metadata_card_mapping_count(self):
        """
        Metadata should list two managed cards.
        """
        card_metadata_count = len(self.note.metadata["managed-cards-mapping"])
        expected_number = 3
        self.assertEqual(card_metadata_count, expected_number)

    def test_number_created_cards(self):
        """
        A single card for each cloze should be created.
        """
        expected_number = 3
        received_number = self.note.cards.count()
        self.assertEqual(expected_number, received_number)

    # for testing purposes:
    # [...] - gap for an actual question
    # {...} - occluded text that is not part of a question

    def test_question_answer_cloze_one(self):
        """
        Note metadata should correctly indicate card for a given cloze.
        Cards are obtained using note metadata in the _get_cards_from_note_metadata
        helper method.
        """
        expected_question = '[...] {...} {...}'
        expected_answer = '[cloze one] cloze two cloze three'

        self.assertEqual(expected_question, self.cloze_one_card.front)
        self.assertEqual(expected_answer, self.cloze_one_card.back)

    def test_question_answer_cloze_two(self):
        expected_question = '{...} [...] {...}'
        expected_answer = 'cloze one [cloze two] cloze three'

        self.assertEqual(expected_question, self.cloze_two_card.front)
        self.assertEqual(expected_answer, self.cloze_two_card.back)