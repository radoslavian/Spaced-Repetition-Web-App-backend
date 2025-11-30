"""
Card serialization to dict and json formats.
"""
import json
from unittest import skip

from django.test import TestCase

from card_types.models import CardNote
from cards.models import CardTemplate, CardImage
from cards.tests.fake_data import fake_data_objects


class SerializationEmptyOptionalFields(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.card = fake_data_objects.make_fake_card()
        cls.mapped_card = None

    def _test_id(self):
        self.assertEqual(self.mapped_card["id"], self.card.id.hex)

    def _test_created_on(self):
        self.assertEqual(self.mapped_card["created_on"],
                         self.card.created_on.isoformat())

    def _test_last_modified(self):
        self.assertEqual(self.mapped_card["last_modified"],
                         self.card.last_modified.isoformat())

    def _test_front_text(self):
        self.assertEqual(self.mapped_card["front"]["text"],
                         self.card.front)

    def _test_front_images(self):
        self.assertListEqual(self.mapped_card["front"]["images"], [])

    def _test_front_audio(self):
        self.assertIsNone(self.mapped_card["front"]["audio"])

    def _test_back_text(self):
        self.assertEqual(self.mapped_card["back"]["text"],
                         self.card.back)

    def _test_back_images(self):
        self.assertListEqual(self.mapped_card["back"]["images"], [])

    def _test_back_audio(self):
        self.assertIsNone(self.mapped_card["back"]["audio"])

    def _test_template(self):
        self.assertIsNone(self.mapped_card["template"])

    def _test_note(self):
        self.assertIsNone(self.mapped_card["note"])

    def _test_categories(self):
        self.assertListEqual(self.mapped_card["categories"], [])


class CardToDictEmptyFields(SerializationEmptyOptionalFields):
    """
    Case inspecting card serialized (mapped) to a dict and its default values
    for empty fields.
    """
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.mapped_card = dict(cls.card)

    def test_id(self):
        self._test_id()

    def test_created_on(self):
        self._test_created_on()

    def test_last_modified(self):
        self._test_last_modified()

    def test_front_text(self):
        self._test_front_text()

    def test_front_images(self):
        self._test_front_images()

    def test_front_audio(self):
        self._test_front_audio()

    def test_back_text(self):
        self._test_back_text()

    def test_back_images(self):
        self._test_back_images()

    def test_back_audio(self):
        self._test_back_audio()

    def test_template(self):
        self._test_template()

    def test_note(self):
        self._test_note()

    def test_categories(self):
        self._test_categories()


class CardToJsonEmptyFields(SerializationEmptyOptionalFields):
    """
    Case inspecting card serialized (mapped) to json and its default values
    for empty fields.
    """
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.mapped_card = json.loads(cls.card.jsonify())

    def test_id(self):
        self._test_id()

    def test_created_on(self):
        self._test_created_on()

    def test_last_modified(self):
        self._test_last_modified()

    def test_front_text(self):
        self._test_front_text()

    def test_front_images(self):
        self._test_front_images()

    def test_front_audio(self):
        self._test_front_audio()

    def test_back_text(self):
        self._test_back_text()

    def test_back_images(self):
        self._test_back_images()

    def test_back_audio(self):
        self._test_back_audio()

    def test_template(self):
        self._test_template()

    def test_note(self):
        self._test_note()

    def test_categories(self):
        self._test_categories()


class SerializationWithOptionalFields(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.card = fake_data_objects.make_fake_card()
        cls.set_template()
        cls.set_images()
        cls.set_sound_fields()
        cls.card.note = CardNote.objects.create()
        cls.card.categories.set([fake_data_objects.make_fake_category()
                                 for _ in range(2)])
        cls.card.save()
        cls.mapped_card = None

    @classmethod
    def set_sound_fields(cls):
        cls.card.front_audio = fake_data_objects.add_sound_entry_to_database(
            fake_data_objects.placeholder_audio_files[0])[0]
        cls.card.back_audio = fake_data_objects.add_sound_entry_to_database(
            fake_data_objects.placeholder_audio_files[1])[0]

    @classmethod
    def set_card_side_images(cls, images, side="front"):
        for image in images:
            CardImage.objects.create(image=image,
                                     card=cls.card,
                                     side=side)

    @classmethod
    def set_images(cls):
        images = [
            fake_data_objects.get_instance_from_image(
                fake_data_objects.gifs[0]),
            fake_data_objects.get_instance_from_image(
                fake_data_objects.gifs[1])]
        cls.front_images = images
        cls.back_images = images[::-1]

        cls.set_card_side_images(cls.front_images, "front")
        cls.set_card_side_images(cls.back_images, "back")

    @classmethod
    def set_template(cls):
        cls.template = CardTemplate.objects.create(
            **fake_data_objects.get_fake_template_data())
        cls.card.template = cls.template

    def _test_template(self):
        self.assertEqual(self.card.template.id.hex,
                         self.mapped_card["template"])

    def _test_images(self):
        front_images = [image.id.hex for image in self.front_images]
        back_images = [image.id.hex for image in self.back_images]
        self.assertEqual(front_images, self.card["front"]["images"])
        self.assertEqual(back_images, self.card["back"]["images"])

    def _test_audio(self):
        self.assertEqual(self.card.front_audio.id.hex,
                         self.card["front"]["audio"])
        self.assertEqual(self.card.back_audio.id.hex,
                         self.card["back"]["audio"])

    def _test_note(self):
        self.assertEqual(self.card.note.id.hex, self.card["note"])

    def _test_categories(self):
        categories = [category.id.hex
                      for category in self.card.categories.all()]
        self.assertListEqual(categories, self.card["categories"])


class CardToDict(SerializationWithOptionalFields):
    """
    Card to dict serialization with optional fields filled with data.
    """
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.mapped_card = dict(cls.card)

    def test_template(self):
        self._test_template()

    def test_images(self):
        self._test_images()

    def test_audio(self):
        self._test_audio()

    def test_note(self):
        self._test_note()

    def test_categories(self):
        self._test_categories()


class CardToJson(SerializationWithOptionalFields):
    """
    Card to json serialization with optional fields filled with data.
    """
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.mapped_card = json.loads(cls.card.jsonify())

    def test_template(self):
        self._test_template()

    def test_images(self):
        self._test_images()

    def test_audio(self):
        self._test_audio()

    def test_note(self):
        self._test_note()

    def test_categories(self):
        self._test_categories()