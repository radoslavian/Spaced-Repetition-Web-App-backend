from hashlib import sha1
from unittest import skip
from django.core.files import File
from django.test import TestCase
from cards.models import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from cards.tests.fake_data import fake, fake_data_objects


class ImageTests(TestCase):
    @skip
    def test_image_embedding_in_card(self):
        pass

    @skip
    def test_image_embedding_in_templates(self):
        pass

    def test_image_hash_validity(self):
        small_gif = SimpleUploadedFile(name=fake.file_name(extension="gif"),
                                       content=fake_data_objects.gifs[0],
                                       content_type="image/gif")
        small_gif_sha1_digest = sha1(small_gif.open().read()).hexdigest()
        image_in_db = Image(image=File(small_gif))
        image_in_db.save()
        self.assertEqual(small_gif_sha1_digest, image_in_db.sha1_digest)