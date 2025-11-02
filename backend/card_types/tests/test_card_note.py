from unittest.mock import Mock, patch
from django.test import TestCase

from card_types.card_managers.exceptions import InvalidCardType
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
        self.card_note = CardNote.objects.create()
        self.card_1 = Card.objects.create(**self.card_1_data,
                                          note=self.card_note)
        self.card_2 = Card.objects.create(**self.card_2_data,
                                          note=self.card_note)

    def tearDown(self):
        # deleting a note results in dropping related cards
        self.card_note.id and self.card_note.delete()

    def test_note_to_card_reference(self):
        """
        The CardNote instance should reference (show) managed cards.
        """
        cards = self.card_note.cards.all()
        self.assertIn(self.card_1, cards)
        self.assertIn(self.card_2, cards)

    def test_card_to_note_reference(self):
        """
        The Card instance should reference a note.
        """
        self.assertIs(self.card_1.note, self.card_note)
        self.assertIs(self.card_2.note, self.card_note)

    def test_deleting_cards(self):
        """
        Deleting both of the related to the note cards shouldn't cause
        deletion of the note.
        """
        self._delete_cards()
        self.card_note.refresh_from_db()
        self.assertTrue(self.card_note.id)

    def _delete_cards(self):
        for card in self.card_1, self.card_2:
            card.id and card.delete()

    def test_deleting_card(self):
        self.card_1.delete()
        expected_number = 1
        received_number = self.card_note.cards.count()
        self.assertEqual(expected_number, received_number)

    def test_deleting_note(self):
        """
        Deleting a note should cause deletion of related cards.
        """
        self.card_note.delete()
        expected_number = 0
        self.assertEqual(Card.objects.count(), expected_number)


class SavingCards(TestCase):
    """
    Creating/updating cards using a selected card manager.
    Using a card manager specified in the card_type field for creating new
    cards or updating existing ones.
    """
    def setUp(self):
        self.note = CardNote.objects.create(card_type="test_type")
        self.test_card_type = Mock()
        self.test_card_type.return_value.save_cards = Mock()
        self.fake_type_managers = {"test_type": self.test_card_type}

    def tearDown(self):
        self.note.delete()
        del self.fake_type_managers
        del self.test_card_type

    def test_receiving_note_instance(self):
        """
        The constructor receives an instance of the CardNote.
        The class instance constructor specified in the card_type field
        receives an instance of the CardNote model.
        """
        with patch("card_types.models.type_managers", self.fake_type_managers):
            self.note.save_cards()
            self.test_card_type.assert_called_once_with(self.note)

    def test_saving_note(self):
        """
        .save_cards() must be called on an instance from the card_type field.
        """
        with patch("card_types.models.type_managers", self.fake_type_managers):
            self.note.save_cards()
            self.test_card_type.return_value.save_cards.assert_called_once()

    def test_incorrect_type_name(self):
        """
        An attempt to invoke an undefined card type name should raise an error.
        """
        self.note.card_type = "invalid-card-type"
        self.note.save()
        with patch("card_types.models.type_managers", self.fake_type_managers):
            self.assertRaises(InvalidCardType, self.note.save_cards)