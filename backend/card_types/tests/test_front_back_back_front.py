import json
from unittest import skip

from django.test import TestCase

from card_types.models import CardNote
from cards.models import Card, CardTemplate, CardImage, Category
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


class ImageTestData:
    @classmethod
    def prepare_images(cls):
        cls.front_image = fake_data_objects.get_instance_from_image(
            fake_data_objects.gifs[0])
        cls.back_image = fake_data_objects.get_instance_from_image(
            fake_data_objects.gifs[1])

    @classmethod
    def add_note_description(cls):
        cls.card_description = {
            "front": {
                "text": "some front text",
                "images": [cls.front_image.id.hex]
            },
            "back": {
                "text": "some back text",
                "images": [cls.back_image.id.hex]
            },
        }

    def create_note(self):
        note_description = json.dumps(self.card_description)
        self.note = CardNote.objects.create(
            card_description=note_description,
            card_type="front-back-back-front")

    def load_cards(self):
        note_metadata = json.loads(self.note.metadata)
        self.front_back_card = self.note.cards.get(
            id__exact=note_metadata["front-back-card-id"])
        self.back_front_card = self.note.cards.get(
            id__exact=note_metadata["back-front-card-id"])


class ImageEntry(TestCase, ImageTestData):
    @classmethod
    def setUpTestData(cls):
        cls.prepare_images()
        cls.add_note_description()

    def setUp(self):
        self.create_note()
        self.load_cards()

    def tearDown(self):
        self.note.delete()

    def test_number_of_entries(self):
        """
        Should create 4 entries in CardImage (2 entries for each card).
        """
        expected_single_card_number = 2
        expected_total_number = 4
        front_back_card_number = self.front_back_card.images.count()
        back_front_card_number = self.back_front_card.images.count()
        total_number = CardImage.objects.count()

        self.assertEqual(front_back_card_number, expected_single_card_number)
        self.assertEqual(back_front_card_number, expected_single_card_number)
        self.assertEqual(expected_total_number, total_number)

    def test_front_back_entries(self):
        front_image = self.get_front_image(self.front_back_card)
        back_image = self.get_back_image(self.front_back_card)

        self.assertTrue(all([front_image, back_image]))
        self.assertEqual(front_image.id, self.front_image.id)
        self.assertEqual(back_image.id, self.back_image.id)

    def test_back_front_entries(self):
        front_image = self.get_front_image(self.back_front_card)
        back_image = self.get_back_image(self.back_front_card)

        self.assertEqual(front_image, self.back_image)
        self.assertEqual(back_image, self.front_image)

    @staticmethod
    def get_image(card, side):
        return CardImage.objects.filter(
            card=card, side__exact=side).first().image

    def get_front_image(self, card):
        return self.get_image(card, side="front")

    def get_back_image(self, card):
        return self.get_image(card, side="back")


class NoteWithImagesUpdate(TestCase, ImageTestData):
    @classmethod
    def setUpTestData(cls):
        cls.prepare_images()
        cls.add_note_description()
        front = {**cls.card_description["front"],
                 "images": [cls.front_image.id.hex,
                            cls.back_image.id.hex]}
        cls.updated_card_description = {
            "front": front,
            "back": {
                "text": "some back text"
            },
        }

    def setUp(self):
        self.create_note()
        self.load_cards()

    def create_note(self):
        super().create_note()
        self.note.card_description = json.dumps(self.updated_card_description)
        self.note.save()

    def tearDown(self):
        self.note.delete()

    def test_number_images(self):
        """
        Number of created image entries.
        Should remain the same after a note update.
        """
        expected_number_of_image_entries = 4
        received_number_of_image_entries = CardImage.objects.count()
        self.assertEqual(expected_number_of_image_entries,
                         received_number_of_image_entries)

    def test_number_images_front_back(self):
        expected_number_of_front_images = 2
        expected_number_of_back_images = 0
        received_number_of_front_images = self.count_front_images(
            self.front_back_card)
        received_number_of_back_images = self.count_back_images(
            self.front_back_card)

        self.assertEqual(expected_number_of_front_images,
                         received_number_of_front_images)
        self.assertEqual(expected_number_of_back_images,
                         received_number_of_back_images)

    def test_number_images_back_front(self):
        expected_number_of_front_images = 0
        expected_number_of_back_images = 2
        received_number_of_front_images = self.count_front_images(
            self.back_front_card)
        received_number_of_back_images = self.count_back_images(
            self.back_front_card)

        self.assertEqual(expected_number_of_front_images,
                         received_number_of_front_images)
        self.assertEqual(expected_number_of_back_images,
                         received_number_of_back_images)

    @staticmethod
    def count_images(card, side):
        return CardImage.objects.filter(card=card, side__exact=side).count()

    def count_front_images(self, card):
        return self.count_images(card, "front")

    def count_back_images(self, card):
        return self.count_images(card, "back")


class CategoriesInDescription(TestCase):
    """
    Adding categories to double-sided cards.
    """
    @classmethod
    def setUpTestData(cls):
        cls.categories = [Category.objects.create(name=category_name)
                          for category_name in ("category 1", "category 2",)]
        cls.card_description = json.dumps({
            "front": {
                "text": "some front text"
            },
            "back": {
                "text": "some back text"
            },
            "categories": [category.id.hex for category in cls.categories]
        })
        cls.note = CardNote.objects.create(
            card_description=cls.card_description,
            card_type="front-back-back-front")

    def test_front_back_card(self):
        """
        Front-back card is created with categories.
        """
        front_back_card_id = json.loads(
            self.note.metadata)["front-back-card-id"]
        front_back_card = Card.objects.get(id__exact=front_back_card_id)

        self._assert_categories_in(front_back_card)

    def test_back_front_card(self):
        """
        Back-front card is created with categories.
        """
        back_front_card_id = json.loads(
            self.note.metadata)["back-front-card-id"]
        back_front_card = Card.objects.get(id__exact=back_front_card_id)

        self._assert_categories_in(back_front_card)

    def _assert_categories_in(self, card):
        expected_no_categories = 2
        received_no_categories = card.categories.count()
        expected_categories = {category.id for category in self.categories}
        received_categories = {category.id for category in
                               card.categories.all()}
        self.assertEqual(received_no_categories, expected_no_categories)
        self.assertSetEqual(received_categories, expected_categories)


class SingleSidedToTwoSided(TestCase):
    """
    Creating a two-sided card from a single-sided one.
    """
    @classmethod
    def setUpTestData(cls):
        cls.card = fake_data_objects.make_fake_card()
        cls.front = cls.card.front
        cls.back = cls.card.back
        cls.card_original_id = cls.card.id.hex
        cls.note = CardNote.from_card(cls.card, "front-back-back-front")
        cls.card.refresh_from_db()

    def test_note_created(self):
        self.assertTrue(self.note.id)

    def test_source_card_unchanged(self):
        """
        The source card shouldn't be overwritten.
        """
        self.assertEqual(self.card.id.hex, self.card_original_id)
        self.assertEqual(self.card.front, self.front)
        self.assertEqual(self.card.back, self.back)

    def test_source_card_references_note(self):
        self.assertEqual(self.card.note.id, self.note.id)

    def test_number_attached_cards(self):
        """
        Test number of cards attached to the note.
        """
        expected_value = 2
        value_received_from_note = self.note.cards.count()
        value_received_from_db = Card.objects.count()

        self.assertEqual(expected_value, value_received_from_note)
        self.assertEqual(expected_value, value_received_from_db)

    def test_back_front_card_exists(self):
        back_front_card = self.note.cards.exclude(
            id__exact=self.card_original_id).first()
        self.assertNotEqual(back_front_card.id, self.card.id)
        self.assertTrue(back_front_card.id)