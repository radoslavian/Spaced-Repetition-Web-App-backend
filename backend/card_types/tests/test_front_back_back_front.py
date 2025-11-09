import json
from unittest import skip

from django.test import TestCase

from card_types.models import CardNote
from cards.models import Card, CardTemplate
from cards.tests.fake_data import fake_data_objects


class CreatingCardsFromNote(TestCase):
    """
    Creating a basic card from the note (with text fields only).
    """
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


class RecreatingCards(TestCase):
    """
    Recreating deleted cards from the note.
    """
    card_description = {
        "front": {
            "text": "some front text"
        },
        "back": {
            "text": "some back text"
        }
    }

    def setUp(self):
        self.note = CardNote.objects.create(
            card_description=json.dumps(self.card_description),
            card_type="front-back-back-front")
        self.metadata = json.loads(self.note.metadata)

    def tearDown(self):
        self.note.delete()

    def test_deleting_single_card(self):
        front_back_card = Card.objects.get(
            id=self.metadata["front-back-card-id"])
        front_back_card.delete()
        self.note.save_cards()

        expected_number = 2
        received_number = Card.objects.count()
        self.assertEqual(expected_number, received_number)

    def test_deleting_both_cards(self):
        Card.objects.all().delete()
        self.note.save_cards()

        expected_number = 2
        received_number = Card.objects.count()
        self.assertEqual(expected_number, received_number)


class CreatingCardsFromNoteWithFields(TestCase):
    """
    Creating cards with fields other than front and back text.
    """
    template_description = {
        "title": "example template",
        "description": "template for testing",
        "body": '{% extends  "fallback.html" %}'
    }

    @classmethod
    def setUpTestData(cls):
        cls._prepare_template()
        cls._prepare_audio_entries()
        cls.cards_description = {
            "front": {
                "text": "some front text",
                "audio": cls.front_audio.id.hex
            },
            "back": {
                "text": "some back text",
                "audio": cls.back_audio.id.hex
            },
            "template": cls.template.id.hex
        }
        cls._create_note()
        cls._get_cards()

    @classmethod
    def _prepare_audio_entries(cls):
        cls.front_audio, _ = fake_data_objects.add_sound_entry_to_database(
            fake_data_objects.placeholder_audio_files[0])
        cls.back_audio, _ = fake_data_objects.add_sound_entry_to_database(
            fake_data_objects.placeholder_audio_files[1])

    @classmethod
    def _get_cards(cls):
        front_back_card_id = json.loads(
            cls.note.metadata)["front-back-card-id"]
        cls.front_back_card = Card.objects.get(id__exact=front_back_card_id)
        back_front_card_id = json.loads(
            cls.note.metadata)["back-front-card-id"]
        cls.back_front_card = Card.objects.get(id__exact=back_front_card_id)

    @classmethod
    def _prepare_template(cls):
        cls.template = CardTemplate.objects.create(**cls.template_description)

    @classmethod
    def _create_note(cls):
        card_description = json.dumps(cls.cards_description)
        cls.note = CardNote.objects.create(
            card_description=card_description,
            card_type="front-back-back-front")

    def test_template_cards(self):
        """
        Cards created from the note should reference a template.
        """
        for card in Card.objects.all():
            self.assertTrue(card.template)
            self.assertEqual(card.template.id, self.template.id)

    def test_front_audio_front_back(self):
        """
        Front audio reference on a front-back card.
        """
        self.assertTrue(self.front_back_card.front_audio)
        self.assertEqual(self.front_back_card.front_audio.id,
                         self.front_audio.id)

    def test_front_audio_back_front(self):
        """
        Front audio reference on a back-front card.
        """
        self.assertTrue(self.back_front_card.front_audio)
        self.assertEqual(self.back_front_card.front_audio.id,
                         self.back_audio.id)

    def test_back_audio_front_back(self):
        """
        Back audio reference on a front-back card.
        """
        self.assertTrue(self.front_back_card.back_audio)
        self.assertEqual(self.front_back_card.back_audio.id,
                         self.back_audio.id)

    def test_back_audio_back_front(self):
        """
        Back audio reference on a back-front card.
        """
        self.assertTrue(self.back_front_card.back_audio)
        self.assertEqual(self.back_front_card.back_audio.id,
                         self.front_audio.id)