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
        self.assertEqual(self.mapped_card["_front"]["text"],
                         self.card.front)

    def _test_front_images(self):
        self.assertListEqual(self.mapped_card["_front"]["images"], [])

    def _test_front_audio(self):
        self.assertIsNone(self.mapped_card["_front"]["audio"])

    def _test_back_text(self):
        self.assertEqual(self.mapped_card["_back"]["text"],
                         self.card.back)

    def _test_back_images(self):
        self.assertListEqual(self.mapped_card["_back"]["images"], [])

    def _test_back_audio(self):
        self.assertIsNone(self.mapped_card["_back"]["audio"])

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
        self.assertEqual(front_images, self.card["_front"]["images"])
        self.assertEqual(back_images, self.card["_back"]["images"])

    def _test_audio(self):
        self.assertEqual(self.card.front_audio.id.hex,
                         self.card["_front"]["audio"])
        self.assertEqual(self.card.back_audio.id.hex,
                         self.card["_back"]["audio"])

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
    .jsonify() receives no arguments.
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


class JsonifySpecificFields(TestCase):
    """
    Jsonifying fields specified in the 'fields' argument.
    """
    @classmethod
    def setUpTestData(cls):
        cls.card = fake_data_objects.make_fake_card()
        number_of_categories = 2
        cls.categories = fake_data_objects.make_fake_categories(
            number_of_categories)
        cls.template = fake_data_objects.make_fake_template()
        cls.card.template = cls.template
        cls.card.categories.set(cls.categories)
        cls.card.save()

    def test_front(self):
        jsonified = json.loads(self.card.jsonify(fields=["_front"]))
        number_of_keys = len(jsonified.keys())
        expected_no_keys = 1
        self.assertEqual(number_of_keys, expected_no_keys)
        self.assertEqual(jsonified["_front"]["text"], self.card.front)

    def test_plain_field(self):
        """
        Single-value field (template in this instance).
        """
        jsonified = json.loads(self.card.jsonify(fields=["template"]))
        self.assertEqual(jsonified["template"], self.card.template_id_hex)

    def test_list_values(self):
        """
        Should output list of values (categories in this case).
        """
        jsonified = json.loads(self.card.jsonify(fields=["categories"]))
        self.assertListEqual(jsonified["categories"],
                             self.card.categories_ids_hex)

    def test_invalid_fields(self):
        """
        All requested fields are invalid.
        """
        invalid_fields = ["invalid_1", "invalid_2"]
        expected_message = "Invalid card fields: ['invalid_1', 'invalid_2']"

        with self.assertRaisesMessage(KeyError, expected_message):
            self.card.jsonify(fields=invalid_fields)

    def test_valid_invalid_field(self):
        """
        One out of two of the requested fields is invalid.
        """
        requested_fields = ["note", "invalid_field"]
        expected_message = "Invalid card fields: ['invalid_field']"

        with self.assertRaisesMessage(KeyError, expected_message):
            self.card.jsonify(fields=requested_fields)