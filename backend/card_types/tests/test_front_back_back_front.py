import json
from unittest import skip

from django.test import TestCase

from card_types.models import CardNote
from cards.models import Card


class CreatingCardsFromNote(TestCase):
    @classmethod
    def setUpTestData(cls):
        note = {
            "front": {
                "text": "some front text"
            },
            "back": {
                "text": "some back text"
            }
        }
        card_description = json.dumps(note)
        cls.note = CardNote.objects.create(card_description=card_description,
                                           card_type="front-back-back-front")
        cls.note_metadata = json.loads(cls.note.metadata)

    def test_backref(self):
        """
        Created cards should be available through a backreference.
        """
        all_cards = Card.objects.all()
        card_1, card_2 = list(self.note.cards.all())

        self.assertIn(card_1, all_cards)
        self.assertIn(card_2, all_cards)

    def test_number_of_cards_created(self):
        """
        Creating a note should save two cards.
        """
        expected_number = 2
        received_number = Card.objects.count()
        self.assertEqual(expected_number, received_number)

    def test_front_back(self):
        """
        Metadata should store front-back card id.
        """
        front_back_card = Card.objects.get(
            id=self.note_metadata["front-back-card-id"])
        front = json.loads(self.note.card_description)["front"]["text"]
        back = json.loads(self.note.card_description)["back"]["text"]

        self.assertEqual(front_back_card.front, front)
        self.assertEqual(front_back_card.back, back)

    def test_back_front(self):
        """
        Metadata should store back-front card id.
        """
        back_front_card = Card.objects.get(
            id=self.note_metadata["back-front-card-id"])
        front = json.loads(self.note.card_description)["back"]["text"]
        back = json.loads(self.note.card_description)["front"]["text"]

        self.assertEqual(back_front_card.front, front)
        self.assertEqual(back_front_card.back, back)


class UpdatingNote(TestCase):
    card_description = {
        "front": {
            "text": "some front text"
        },
        "back": {
            "text": "some back text"
        }
    }
    updated_description = {
        "front": {
            "text": "altered front text"
        },
        "back": {
            "text": "altered back text"
        }
    }

    @classmethod
    def setUpTestData(cls):
        cls._create_note()
        cls._save_original_card_ids()

        cls._update_note()
        cls._save_updated_card_ids()

    @classmethod
    def _save_updated_card_ids(cls):
        cls.front_back_card_id = json.loads(
            cls.note.metadata)["front-back-card-id"]
        cls.back_front_card_id = json.loads(
            cls.note.metadata)["back-front-card-id"]

    @classmethod
    def _save_original_card_ids(cls):
        cls.original_back_front_card_id = json.loads(
            cls.note.metadata)["back-front-card-id"]
        cls.original_front_back_card_id = json.loads(
            cls.note.metadata)["front-back-card-id"]

    @classmethod
    def _create_note(cls):
        card_description = json.dumps(cls.card_description)
        cls.note = CardNote.objects.create(card_description=card_description,
                                           card_type="front-back-back-front")

    @classmethod
    def _update_note(cls):
        cls.note.card_description = json.dumps(cls.updated_description)
        cls.note.save()

    def test_number_of_cards(self):
        """
        Number of cards shouldn't change.
        Additional calls to CardNote.save() shouldn't create any new cards.
        """
        expected_number = 2
        received_number = Card.objects.count()
        self.assertEqual(expected_number, received_number)

    def test_front_back_text(self):
        card = Card.objects.get(id=self.front_back_card_id)
        expected_front_text = self.updated_description["front"]["text"]
        expected_back_text = self.updated_description["back"]["text"]

        self.assertEqual(card.front, expected_front_text)
        self.assertEqual(card.back, expected_back_text)

    def test_back_front_text(self):
        card = Card.objects.get(id=self.back_front_card_id)
        expected_front_text = self.updated_description["back"]["text"]
        expected_back_text = self.updated_description["front"]["text"]

        self.assertEqual(card.front, expected_front_text)
        self.assertEqual(card.back, expected_back_text)

    def test_front_back_id(self):
        """
        Card id for the front-back card should stay the same.
        """
        card = Card.objects.get(id=self.front_back_card_id)
        self.assertEqual(card.id.hex, self.original_front_back_card_id)

    def test_back_front_id(self):
        """
        Card id for the back-back card should stay the same.
        """
        card = Card.objects.get(id=self.back_front_card_id)
        self.assertEqual(card.id.hex, self.original_back_front_card_id)