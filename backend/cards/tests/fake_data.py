import random
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from faker import Faker
from cards.models import Card, Image, Category, Sound

fake = Faker()
User = get_user_model()


class FakeData:
    @staticmethod
    def get_fake_card_data():
        return {
            "front": fake.text(100),
            "back": fake.text(100)
        }

    @staticmethod
    def get_fake_template_data():
        return {
            "title": fake.text(60),
            "description": fake.text(300),
            "body": fake.text(300)
        }

    def make_fake_cards(self, number_of_cards):
        return [self.make_fake_card() for _ in range(number_of_cards)]

    @staticmethod
    def make_fake_card():
        return Card.objects.create(front=fake.text(20), back=fake.text(20))

    @staticmethod
    def make_fake_category(category_name=None):
        if not category_name:
            category_name = fake.text(20)
        category = Category.objects.create(name=category_name)
        return category

    def make_fake_users(self, number_of_users):
        return [self.make_fake_user() for _ in range(number_of_users)]

    @staticmethod
    def make_fake_user():
        return User.objects.create(username=fake.profile()["username"])


class Helpers:
    def get_image_instance(self):
        small_gif = self.gifs[0]
        return self.get_instance_from_image(small_gif)

    @staticmethod
    def get_instance_from_image(image):
        image = SimpleUploadedFile(name=fake.file_name(extension="gif"),
                                   content=image,
                                   content_type="image/gif")
        image_in_database = Image(image=image,
                                  description=fake.text(999))
        image_in_database.save()
        return image_in_database

    gifs = [
        (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01'
            b'\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00'
            b'\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        ),
        (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01'
            b'\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00'
            b'\x00\x01\x00\x01\x00\x00\x02\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
    ]

    @staticmethod
    def get_random_gif():
        return (b'\x47\x49\x46\x38\x39\x61\x01\x00\x01'
                + random.randbytes(23)
                + b'\x02\x4c\x01\x00\x3b')

    placeholder_audio_files = [
        (
            b'MM\x00*\x00\x00\x00\x08\x00\x03\x01\x00\x00'
            b'\x03\x00\x00\x00\x01\x00\x01\x00\x00\x01'
            b'\x01\x00\x03\x00\x00\x00\x01\x00\x01\x00\x00'
            b'\x01\x11\x00\x03\x00\x00\x00\x01\x00'
            b'\x00\x00\x00'
        ),
        (
            b'MM\x00*\x00\x00\x00\x08\x00\x03\x01\x00\x00'
            b'\x03\x00\x00\x00\x01\x00\x01\x00\x00\x01'
            b'\x01\x11\x03\x00\x00\x00\x01\x00\x01\x00\x00'
            b'\x01\x11\x00\x03\x00\x00\x00\x01\x00'
            b'\x00\x00\x00'
        )
    ]

    @staticmethod
    def add_soundfile_to_database(placeholder_audio_file):
        file_name = fake.file_name(extension="mp3")
        audio_file = SimpleUploadedFile(
            name=file_name,
            content=placeholder_audio_file,
            content_type="audio/mpeg")
        database_audio_entry = Sound(sound_file=audio_file,
                                     description=fake.text(999))
        database_audio_entry.save()
        return database_audio_entry, file_name


fake_objects = Helpers()
fake_data_objects = FakeData()