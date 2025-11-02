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