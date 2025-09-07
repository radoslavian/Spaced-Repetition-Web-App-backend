from hashlib import sha1

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from cards.models import Sound, Card
from cards.tests.fake_data import fake_data_objects
import uuid


class SoundFileModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        (cls.sound,
         cls.audio_filename) = fake_data_objects.add_sound_entry_to_database(
            fake_data_objects.placeholder_audio_files[0])

    def test_adding_audio_to_database(self):
        sound_id_type = type(self.sound.id)
        self.assertTrue(self.sound.id)
        self.assertIs(sound_id_type, uuid.UUID)

    def test_sound_file_hashing(self):
        sound_file = SimpleUploadedFile(
            "audio file",
            fake_data_objects.placeholder_audio_files[0],
            "audio/mpeg")
        sound_file_sha1_digest = sha1(sound_file.open().read()).hexdigest()
        sound_file_instance_in_db = Sound.objects.get(
            sha1_digest=sound_file_sha1_digest)

        self.assertEqual(sound_file_sha1_digest,
                         sound_file_instance_in_db.sha1_digest)


class SoundsInCards(TestCase):
    def setUp(self):
        self.add_placeholder_sounds()
        self.add_cards()

    def add_cards(self):
        number_of_cards = 2
        self.card_1, self.card_2 = fake_data_objects.make_fake_cards(
            number_of_cards)

    def add_placeholder_sounds(self):
        self.sound_entry_1 = fake_data_objects.add_sound_entry_to_database(
            fake_data_objects.placeholder_audio_files[0])[0]
        self.sound_entry_2 = fake_data_objects.add_sound_entry_to_database(
            fake_data_objects.placeholder_audio_files[1])[0]

    def tearDown(self):
        for Model in [Sound, Card]:
            Model.objects.all().delete()

    def test_sounds_front(self):
        """
        Attaching one sound to multiple cards (front).
        """
        self.card_1.front_audio = self.sound_entry_1
        self.card_2.front_audio = self.sound_entry_1
        self.card_2.back_audio = self.sound_entry_2
        self.save_cards()

        number_of_front_cards = 2
        self.assertEqual(self.sound_entry_1.cards_front.count(),
                         number_of_front_cards)
        self.assertFalse(self.sound_entry_2.cards_front.all())

    def test_sounds_back(self):
        """
        Attaching one sound to multiple cards (back).
        """
        self.card_1.back_audio = self.sound_entry_1
        self.card_2.back_audio = self.sound_entry_1
        self.card_2.front_audio = self.sound_entry_2
        self.save_cards()

        number_of_back_cards = 2
        self.assertEqual(self.sound_entry_1.cards_back.count(),
                         number_of_back_cards)
        self.assertFalse(self.sound_entry_2.cards_back.all())

    def test_related_name_front(self):
        self.card_1.front_audio = self.sound_entry_1
        self.card_2.back_audio = self.sound_entry_1
        self.save_cards()

        expected_number_of_cards = 1
        self.assertEqual(self.sound_entry_1.cards_front.count(),
                         expected_number_of_cards)
        self.assertEqual(self.sound_entry_1.cards_front.first(), self.card_1)

    def test_related_name_back(self):
        self.card_1.back_audio = self.sound_entry_1
        self.card_2.front_audio = self.sound_entry_1
        self.save_cards()

        expected_number_of_cards = 1
        self.assertEqual(self.sound_entry_1.cards_back.count(),
                         expected_number_of_cards)
        self.assertEqual(self.sound_entry_1.cards_back.first(), self.card_1)

    def save_cards(self):
        for card in (self.card_1, self.card_2,):
            card.save()


class HandlingDeletions(TestCase):
    def setUp(self):
        self.add_placeholder_sounds()
        self.card = fake_data_objects.make_fake_card()
        self.card.front_audio = self.sound_entry_front
        self.card.back_audio = self.sound_entry_back
        self.card.save()

    def add_placeholder_sounds(self):
        self.sound_entry_front, self.sound_entry_back = [
            fake_data_objects.add_sound_entry_to_database(placeholder)[0]
            for placeholder in fake_data_objects.placeholder_audio_files
        ]

    def tearDown(self):
        for Model in [Sound, Card]:
            Model.objects.all().delete()

    def test_removing_sound_front(self):
        """
        Removing a sound entry attached to the card's front doesn't cause
        card's deletion.
        """
        self.sound_entry_front.delete()
        self.card.refresh_from_db()

        self.assertTrue(self.card.id)
        # check if field definition's on_delete=models.SET_NULL works:
        self.assertIsNone(self.card.front_audio)

    def test_removing_sound_back(self):
        """
        Removing a sound entry attached to card's back doesn't delete the card.
        """
        self.sound_entry_back.delete()
        self.card.refresh_from_db()

        self.assertTrue(self.card.id)
        # check if field definition's on_delete=models.SET_NULL works:
        self.assertIsNone(self.card.back_audio)

    def test_removing_card_front(self):
        """
        Removing a card doesn't cause deletion of a sound entry attached
        to the card's front.
        """
        self.card.delete()
        self.sound_entry_front.refresh_from_db()

        self.assertIsNotNone(self.sound_entry_front.id)

    def test_removing_card_back(self):
        """
        Removing a card doesn't cause deletion of a sound entry attached
        to the card's back.
        """
        self.card.delete()
        self.sound_entry_back.refresh_from_db()

        self.assertIsNotNone(self.sound_entry_back.id)