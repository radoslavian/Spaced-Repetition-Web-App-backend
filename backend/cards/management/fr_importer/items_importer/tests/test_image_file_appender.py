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

    def test_invalid_path(self):
        """
        Should raise 'FileNotFoundError' if path is incorrect.
        """
        invalid_path = "./fake/path/to/image.png"
        def throw_file_not_found():
            image_instance = ImageFileAppender(invalid_path)

        self.assertRaises(FileNotFoundError, throw_file_not_found)


class AddingExistingFile(TestCase):
    """
    Attempt to add to a database a file that is already there.
    """

    @classmethod
    def setUpTestData(cls):
        cls.file_in_db_path = ("cards/management/fr_importer/"
                               "items_importer/tests/test_data/"
                               "fdb/images/chess_board.jpg")
        cls.instance_1 = ImageFileAppender(cls.file_in_db_path).file_instance
        cls.instance_2 = ImageFileAppender(cls.file_in_db_path).file_instance

    def test_no_new_record(self):
        """
        No new record should be created for an extra addition.
        """
        expected_number_of_images_in_db = 1
        received_number_of_images_in_db = Image.objects.count()
        self.assertEqual(expected_number_of_images_in_db,
                         received_number_of_images_in_db)

    def test_image_instance_returned(self):
        """
        A reference to already existing Image object should be returned.
        In case a file already exists in the database,
        a reference to an instance of a record should be returned.
        """
        self.assertEqual(str(self.instance_1),
                         str(self.instance_2))
