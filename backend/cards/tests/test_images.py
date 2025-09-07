import django.db.utils
from django.db import transaction
from django.test import TestCase
from cards.models import CardImage
from cards.tests.fake_data import fake_data_objects

class CardImageCase(TestCase):
    def setUp(self):
        self.card = fake_data_objects.make_fake_card()
        self.image_in_database = fake_data_objects.get_image_instance()
        self.card_front_image = CardImage(card=self.card,
                                          image=self.image_in_database,
                                          side="front")
        self.card_front_image.save()
        self.card_back_image = CardImage(card=self.card,
                                         image=self.image_in_database,
                                         side="back")
        self.card_back_image.save()

    def tearDown(self):
        for instance in [self.card,
                         self.image_in_database,
                         self.card_front_image,
                         self.card_back_image]:
            if instance.pk:
                instance.delete()

    def test_adding_images_to_card(self):
        """
        card.front_images and .back_images each should have a single image.
        """
        self.assertEqual(len(self.card.front_images), 1)
        self.assertEqual(self.image_in_database.cards.count(), 2)
        self.assertEqual(len(self.card.back_images), 1)

    def test_remove_card_to_image(self):
        """
        Deleting an image from the card: should keep the image file entry
        in the database.
        """
        self.card_front_image.delete()
        self.card_back_image.delete()

        self.assertTrue(self.card.id)
        self.assertTrue(self.image_in_database.id)

    def test_delete_card_keep_image(self):
        """
        Should keep an image instance in the database after deleting the card.
        """
        self.card.delete()
        self.assertRaises(CardImage.DoesNotExist,
                          self.card_front_image.refresh_from_db)
        self.assertTrue(self.image_in_database.id)

    def test_uniqueness_card_image_side(self):
        """
        Should raise an error in an attempt to add (again) an identical
        CardImage instance to the database.
        """

        @transaction.atomic
        def add_once(side):
            card_image = CardImage(card=self.card,
                                       image=self.image_in_database,
                                       side=side)
            card_image.save()

        self.assertRaises(django.db.utils.IntegrityError,
                          lambda: add_once("front"))

    def test_side_check_constraint(self):
        """
        CardImage.side should accept only valid values: 'front' or 'back'.
        """
        save_card_image = transaction.atomic(
            CardImage(card=self.card,
                      image=self.image_in_database,
                      side="fff").save)

        self.assertRaises(django.db.utils.IntegrityError, save_card_image)