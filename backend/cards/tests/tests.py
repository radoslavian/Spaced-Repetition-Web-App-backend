from hashlib import sha1
from random import randint
from unittest import skip
from django.core.files import File
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from cards.models import Card, Image, Sound
from django.core.files.uploadedfile import SimpleUploadedFile
from cards.tests.fake_data import fake, fake_data_objects, Helpers

make_fake_cards = fake_data_objects.make_fake_cards

class FakeUsersCards(TestCase):
    # TODO: Delete this whole class !!!
    user_model = get_user_model()

    def setUp(self):
        self.add_fake_users()
        self.add_fake_cards()

    def get_cards(self):
        """Returns three example cards.
        """
        card_1 = Card.objects.get(front=self.cards_data["first"]["front"])
        card_2 = Card.objects.get(front=self.cards_data["second"]["front"])
        card_3 = Card.objects.get(front=self.cards_data["third"]["front"])
        return card_1, card_2, card_3

    @classmethod
    def get_users(cls):
        """Returns two example users.
        """
        user_1 = cls.user_model.objects.get(username="first_user")
        user_2 = cls.user_model.objects.get(username="second_user")
        return user_1, user_2

    @classmethod
    def add_fake_users(cls):
        user_1 = cls.user_model(username="first_user")
        user_2 = cls.user_model(username="second_user")
        user_1.save()
        user_2.save()

    def add_fake_cards(self):
        self.cards_data = {
            "first": self.fake_card_data(),
            "second": self.fake_card_data(),
            "third": self.fake_card_data()
        }
        for key in self.cards_data:
            Card(**self.cards_data[key]).save()

    @staticmethod
    def fake_card_data():
        fake_text_len = (30, 100,)
        return {
            "front": fake.text(randint(*fake_text_len)),
            "back": fake.text(randint(*fake_text_len))
        }

    def get_card_user(self):
        card, *_ = self.get_cards()
        user, _ = self.get_users()
        return card, user


class CardCategories(FakeUsersCards, Helpers):
    def test_card_single_category(self):
        category_name = fake.text(20)
        card, category = self.card_with_category(category_name)

        self.assertEqual(len(card.categories.all()), 1)
        self.assertEqual(card.categories.first().name, category_name)

    def test_deleting_category_keeps_card(self):
        card, category = self.card_with_category()
        category.delete()
        self.assertTrue(card.id)

    def test_deleting_card_keeps_category(self):
        card, category = self.card_with_category()
        card.delete()
        self.assertFalse(card.id)
        self.assertTrue(category.id)

    def test_card_multiple_categories(self):
        card_1, card_2, _ = self.get_cards()
        category_names = [fake.text(20) for _ in range(4)]
        categories = [fake_data_objects.make_fake_category(name)
                      for name in category_names]
        card_1.categories.add(*categories[:2])
        card_2.categories.add(*categories[2:])
        [card.save() for card in (card_1, card_2,)]
        card_1_categories = card_1.categories.all()
        card_2_categories = card_2.categories.all()

        self.assertEqual(len(card_1_categories), 2)
        self.assertEqual(len(card_2_categories), 2)
        self.assertFalse(card_1_categories[1] in card_2_categories)
        self.assertTrue(card_1_categories[0].name in category_names[:2])
        self.assertTrue(card_2_categories[0].name in category_names[2:])
        self.assertFalse(card_2_categories[0].name in category_names[:2])

        category_from_card_1 = card_1_categories[0]
        card_1.categories.set([])
        card_1.save()
        category_from_card_1.refresh_from_db()
        self.assertTrue(category_from_card_1.id)

    def card_with_category(self, category_name=fake.text(20)):
        card, *_ = self.get_cards()
        category = fake_data_objects.make_fake_category(category_name)
        card.categories.add(category)
        card.save()
        return card, category


class AbsoluteUrls(Helpers, TestCase):
    def setUp(self):
        # this should be inherited from the ApiTestHelpersMixin
        # which currently resides in api.tests
        self.client = APIClient()
        self.user = fake_data_objects.make_fake_user()
        self.client.force_authenticate(user=self.user)
        self.card = make_fake_cards(1)[0]

    def test_card_user_data_canonical_url(self):
        card_user_data = self.card.memorize(self.user)
        canonical_url = reverse("memorized_card",
                                kwargs={"pk": self.card.id,
                                        "user_id": self.user.id})

        self.assertEqual(card_user_data.get_absolute_url(), canonical_url)


class SoundFiles(Helpers, TestCase):
    def setUp(self):
        (self.sound,
         self.audio_filename) = self.add_soundfile_to_database(
            self.placeholder_audio_files[0])

    def test_adding_audio_to_database(self):
        filename_no_extension = self.audio_filename.split(".")[0]
        file_retrieved_from_db = Sound.objects.filter(
            sound_file__contains=filename_no_extension).first()
        self.assertTrue(file_retrieved_from_db)

    def test_sound_file_hashing(self):
        sound_file = SimpleUploadedFile("audio file",
                                        self.placeholder_audio_files[0],
                                        "audio/mpeg")
        sound_file_sha1_digest = sha1(sound_file.open().read()).hexdigest()
        sound_file_instance_in_db = Sound.objects.get(
            sha1_digest=sound_file_sha1_digest)
        self.assertEqual(sound_file_sha1_digest,
                         sound_file_instance_in_db.sha1_digest)


class SoundsInCards(Helpers, TestCase):
    def setUp(self):
        self.card_1, self.card_2 = make_fake_cards(2)
        sound_entries = []
        # valid as long as .placeholder_audio_files has only two elements:
        for placeholder_audio in self.placeholder_audio_files:
            entry_in_db, name = self.add_soundfile_to_database(
                placeholder_audio)
            sound_entries.append({
                "entry": entry_in_db,
                "name": name
            })
        self.sound_entry_1 = sound_entries[0]["entry"]
        self.sound_entry_2 = sound_entries[1]["entry"]

    def test_sounds_front(self):
        """Attaching one sound to multiple cards (front).
        """
        self.card_1.front_audio = self.sound_entry_1
        self.card_2.front_audio = self.sound_entry_1
        self.card_2.back_audio = self.sound_entry_2
        self.card_1.save()
        self.card_2.save()

        self.assertEqual(self.sound_entry_1.cards_front.count(), 2)
        self.assertFalse(self.sound_entry_2.cards_front.all())

    def test_sounds_back(self):
        """Attaching one sound to multiple cards (back).
        """
        self.card_1.back_audio = self.sound_entry_1
        self.card_2.back_audio = self.sound_entry_1
        self.card_2.front_audio = self.sound_entry_1
        self.card_1.save()
        self.card_2.save()

        self.assertEqual(self.sound_entry_1.cards_back.count(), 2)
        self.assertFalse(self.sound_entry_2.cards_back.all())

    def test_related_name_front(self):
        self.card_1.front_audio = self.sound_entry_1
        self.card_2.back_audio = self.sound_entry_1
        self.card_1.save()
        self.card_2.save()

        self.assertEqual(self.sound_entry_1.cards_front.count(), 1)
        self.assertEqual(self.sound_entry_1.cards_front.first(), self.card_1)

    def test_related_name_back(self):
        self.card_1.back_audio = self.sound_entry_1
        self.card_2.front_audio = self.sound_entry_1
        self.card_1.save()
        self.card_2.save()

        self.assertEqual(self.sound_entry_1.cards_back.count(), 1)
        self.assertEqual(self.sound_entry_1.cards_back.first(), self.card_1)

    def test_removing_sound_front(self):
        """Removing sound entry attached to card's front doesn't
        delete the card.
        """
        self.card_1.back_audio = self.sound_entry_1
        card_1_front = self.card_1.front
        self.card_1.save()
        self.sound_entry_1.delete()
        card_from_db = Card.objects.filter(front=card_1_front).first()

        self.assertEqual(card_from_db.front, card_1_front)
        # check if field definition's on_delete=models.SET_NULL works:
        self.assertIsNone(card_from_db.front_audio)

    def test_removing_sound_back(self):
        """Removing sound entry attached to card's back doesn't
        delete the card.
        """
        self.card_1.back_audio = self.sound_entry_1
        card_1_back = self.card_1.back
        self.card_1.save()
        self.sound_entry_1.delete()
        card_from_db = Card.objects.filter(back=card_1_back).first()

        self.assertEqual(card_from_db.back, card_1_back)
        # check if field definition's on_delete=models.SET_NULL works:
        self.assertIsNone(card_from_db.back_audio)

    def test_removing_card_front(self):
        """Removing card doesn't delete sound entry attached
        to the card's front.
        """
        self.card_1.front_audio = self.sound_entry_1
        self.card_1.save()
        self.card_1.delete()
        self.sound_entry_1.refresh_from_db()

        self.assertTrue(self.sound_entry_1)

    def test_removing_card_back(self):
        """Removing card doesn't delete sound entry attached
        to the card's back.
        """
        self.card_1.back_audio = self.sound_entry_1
        self.card_1.save()
        self.card_1.delete()
        self.sound_entry_1.refresh_from_db()

        self.assertTrue(self.sound_entry_1)


class ImageTests(Helpers, TestCase):
    @skip
    def test_image_embedding_in_card(self):
        pass

    @skip
    def test_image_embedding_in_templates(self):
        pass

    def test_image_hash_validity(self):
        small_gif = SimpleUploadedFile(name=fake.file_name(extension="gif"),
                                       content=Helpers.gifs[0],
                                       content_type="image/gif")
        small_gif_sha1_digest = sha1(small_gif.open().read()).hexdigest()
        image_in_db = Image(image=File(small_gif))
        image_in_db.save()
        self.assertEqual(small_gif_sha1_digest, image_in_db.sha1_digest)