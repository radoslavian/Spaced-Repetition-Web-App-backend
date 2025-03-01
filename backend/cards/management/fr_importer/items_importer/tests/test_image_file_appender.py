import os.path
from unittest import skip

from django.test import TestCase

from cards.management.fr_importer.items_importer.modules.file_appenders import \
    ImageFileAppender
from cards.models import Image


class AddingNewFile(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.image_file_path = ("cards/management/fr_importer/"
                                             "items_importer/tests/test_data/"
                                             "fdb/images/teller.png")
        cls.image_file_name = os.path.basename(cls.image_file_path)
        ImageFileAppender(cls.image_file_path).file_instance

    def test_number_of_records(self):
        """
        Only one record for an image should be created.
        """
        all_objects = Image.objects.all()
        expected_number = 1
        self.assertEqual(expected_number, len(all_objects))

    def test_filtering(self):
        """
        Filtering database by a file name should return Image record.
        """
        file_name = r"images/teller.*\.png"
        image_instance = Image.objects.filter(image__iregex=file_name).first()
        self.assertIsNotNone(image_instance)


@skip
class AddingExistingFile(TestCase):
    """
    Attempt to add to a database a file that is already there.
    """
    @classmethod
    def setUpTestData(cls):
        cls.file_in_db_path = "test_data/fdb/images/chess_board.jpg"
        cls.original_image_record = ImageFileAppender(cls.file_in_db_path)
        # etc.... expand

    def test_no_new_record(self):
        """
        No new record should be created for an extra addition.
        """
        ImageFileAppender(self.file_in_db_path)

    def test_image_instance_returned(self):
        """
        A reference to already existing Image object should be returned.
        In case a file with a given name already exists in the database,
        a reference to an instance of a record should be returned.
        """
        image = ImageFileAppender(self.file_in_db_path)
        self.assertIs(image, self.original_image_record)


class AddingNonExistentFile(TestCase):
    """
    Attempt to add a file from an invalid file path.
    """
    @classmethod
    def setUpTestData(cls):
        cls.invalid_file_path = "fake/path/to/image.png"

    def test_invalid_path(self):
        """
        Should throw a 'FileNotFound' error.
        """
        pass
