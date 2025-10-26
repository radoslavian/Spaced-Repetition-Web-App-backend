from unittest import skip
from django.test import TestCase
from cards.models import  Card
from card_types.models import CardNote


class NewCardNote(TestCase):
    """
    Defaults for newly created card note.
    The card is connected to a "note", the note has a type (it is connected to
    a type - a class that manages the cards connected to the note).
    """
    @classmethod
    def setUpTestData(cls):
        cls.card_note_1 = CardNote.objects.create()
        cls.card_note_2 = CardNote.objects.create()

    def test_unique_ids(self):
        self.assertTrue(all([self.card_note_1.id, self.card_note_2.id]))
        self.assertNotEqual(self.card_note_1.id, self.card_note_2.id)

    def test_empty_description(self):
        self.assertFalse(self.card_note_1.card_description)

    def test_empty_metadata(self):
        self.assertFalse(self.card_note_1.metadata)

    def test_empty_card_type(self):
        self.assertFalse(self.card_note_1.card_type)


@skip
class CardReference(TestCase):
    """
    Default behaviour for a Card to CardNote relationship.
    """
    @classmethod
    def setUpTestData(cls):
        cls.card_1_data = {'front': 'card 1 question',
                           'back': 'card 1 answer'}
        cls.card_2_data = {'front': 'card 2 question',
                           'back': 'card 2 answer'}

    def setUp(self):
        self.card_note = CardNote()
        self.card_1 = Card.objects.create(**self.card_1_data,
                                          note=self.card_note)
        self.card_2 = Card.objects.create(**self.card_2_data,
                                          note=self.card_note)

    def test_note_to_card_reference(self):
        """
        The CardNote instance should reference (show) managed cards.
        """
        pass

    def test_card_to_note_reference(self):
        """
        The Card instance should reference a note.
        """
        pass

    def test_deleting_card(self):
        """
        Deleting both of the related to the note cards shouldn't cause
        deletion of the note.
        """
        pass

    def test_deleting_note(self):
        """
        Deleting the note shouldn't cause deletion of cards.
        References should be set to None.
        """
        pass