from unittest.mock import Mock, patch
from django.test import TestCase

from card_types.card_managers.exceptions import InvalidCardType
from cards.models import  Card
from card_types.models import CardNote
from cards.tests.fake_data import fake_data_objects


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
        self.test_card_type = Mock()
        self.test_card_type.return_value.save_cards = Mock()
        self.fake_type_managers = {"test_type": self.test_card_type}
        with self._patch_managers():
            self.note = CardNote.objects.create(card_type="test_type")

    def tearDown(self):
        self.note.delete()
        Card.objects.all().delete()
        del self.fake_type_managers
        del self.test_card_type

    def test_receiving_note_instance(self):
        """
        The constructor receives an instance of the CardNote.
        The class instance constructor specified in the card_type field
        receives an instance of the CardNote model.
        """
        self.test_card_type.assert_called_once_with(self.note)

    def test_saving_note(self):
        """
        .save_cards() must be called on an instance from the card_type field.
        """
        with self._patch_managers():
            self.test_card_type.return_value.save_cards.assert_called_once()

    def test_incorrect_type_name(self):
        """
        An attempt to invoke an undefined card type name should raise an error.
        """
        self.note.delete()
        self.note.card_type = "invalid-card-type"
        with self._patch_managers():
            self.assertRaises(InvalidCardType, self.note.save)

        notes_created = 0
        cards_in_db = 0
        self.assertEqual(notes_created, CardNote.objects.count())
        self.assertEqual(cards_in_db, Card.objects.count())

    def _patch_managers(self):
        return patch("card_types.models.type_managers",
                     self.fake_type_managers)

    def test_updating_note(self):
        """
        Updating a note should update attached cards.
        """
        self.note.save_cards = Mock()
        self.note.card_description = "new value"
        self.note.save()
        self.note.save_cards.assert_called_once()

    def test_empty_card_type(self):
        """
        Not-None .card_type_instance is required to update associated cards.
        If it is None, no cards are updated.
        """
        note = CardNote.objects.create()
        self.assertIsNone(note.card_type_instance)


class NoteFromCardFromNote(TestCase):
    def setUp(self):
        self.card = fake_data_objects.make_fake_card()

    def tearDown(self):
        Card.objects.all().delete()
        CardNote.objects.all().delete()

    def test_invalid_card_type(self):
        """
        No new cards and notes should be created if an exception occurs.
        """
        notes_created = 0
        cards_in_db = 1
        self.assertRaises(InvalidCardType, self._note_from_with_invalid_card_type)
        self.assertEqual(notes_created, CardNote.objects.count())
        self.assertEqual(cards_in_db, Card.objects.count())

    def _note_from_with_invalid_card_type(self):
        invalid_card_type = "invalid-card-type"
        CardNote.from_card(self.card, invalid_card_type)