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


class SoundInCards(TestCase):
    def setUp(self):
        self.card_1, self.card_2 = fake_data_objects.make_fake_cards(2)
        sound_entries = []
        # valid as long as .placeholder_audio_files has only two elements:
        for placeholder_audio in fake_data_objects.placeholder_audio_files:
            entry_in_db, name = fake_data_objects.add_sound_entry_to_database(
                placeholder_audio)
            sound_entries.append({
                "entry": entry_in_db,
                "name": name
            })
        self.sound_entry_1 = sound_entries[0]["entry"]
        self.sound_entry_2 = sound_entries[1]["entry"]

    def tearDown(self):
        Sound.objects.all().delete()

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
