"""
Card serialization to dict and json formats.
"""
from django.test import TestCase

from card_types.models import CardNote
from cards.models import Card, CardTemplate, CardImage
from cards.tests.fake_data import fake_data_objects


class DictSerializationEmptyOptionalFields(TestCase):
    """
    Case inspecting card serialized (mapped) to a dict and its default values
    for empty fields.
    """
    @classmethod
    def setUpTestData(cls):
        cls.front_text = "front text"
        cls.back_text = "back text"
        cls.card = Card.objects.create(
            front=cls.front_text,
            back=cls.back_text)
        cls.mapped_card = dict(cls.card)

    def test_id(self):
        self.assertEqual(self.mapped_card["id"], self.card.id)

    def test_created_on(self):
        self.assertEqual(self.mapped_card["created_on"],
                         self.card.created_on)

    def test_last_modified(self):
        self.assertEqual(self.mapped_card["last_modified"],
                         self.card.last_modified)

    def test_front_text(self):
        self.assertEqual(self.mapped_card["front"]["text"],
                         self.front_text)

    def test_front_images(self):
        self.assertListEqual(self.mapped_card["front"]["images"], [])

    def test_front_audio(self):
        self.assertIsNone(self.mapped_card["front"]["audio"])

    def test_back_text(self):
        self.assertEqual(self.mapped_card["back"]["text"],
                         self.back_text)

    def test_back_images(self):
        self.assertListEqual(self.mapped_card["back"]["images"], [])

    def test_back_audio(self):
        self.assertIsNone(self.mapped_card["back"]["audio"])

    def test_template(self):
        self.assertIsNone(self.mapped_card["template"])

    def test_note(self):
        self.assertIsNone(self.mapped_card["note"])

    def test_categories(self):
        self.assertListEqual(self.mapped_card["categories"], [])


class SerializationSetup:
    @classmethod
    def setup_test_data(cls):
        cls.card = fake_data_objects.make_fake_card()
        cls.set_template()
        cls.set_images()
        cls.set_sound_fields()
        cls.card.note = CardNote.objects.create()
        cls.card.categories.set([fake_data_objects.make_fake_category()
                                 for _ in range(2)])
        cls.card.save()
        cls.mapped_card = dict(cls.card)

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


class DictSerializationWithOptionalFields(TestCase, SerializationSetup):
    """
    Optional fields are filled with data.
    """
    @classmethod
    def setUpTestData(cls):
        cls.setup_test_data()

    def test_template(self):
        self.assertEqual(self.card.template, self.mapped_card["template"])

    def test_images(self):
        self.assertEqual(self.front_images, self.card["front"]["images"])
        self.assertEqual(self.back_images, self.card["back"]["images"])

    def test_audio(self):
        self.assertEqual(self.card.front_audio, self.card["front"]["audio"])
        self.assertEqual(self.card.back_audio, self.card["back"]["audio"])

    def test_note(self):
        self.assertEqual(self.card.note, self.card["note"])

    def test_categories(self):
        categories = list(self.card.categories.all())
        self.assertListEqual(categories, self.card["categories"])