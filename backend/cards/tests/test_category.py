from typing import List
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.deletion import ProtectedError
from django.db.utils import IntegrityError
from django.test import TestCase
from cards.models import Card, Category
from cards.tests.fake_data import fake, fake_data_objects


class CategoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        category_name_len = 20
        cls.top_level_category_name = fake.text(category_name_len)
        cls.first_sibling_category_name = fake.text(category_name_len)
        cls.second_sibling_category_name = fake.text(category_name_len)

    def setUp(self):
        self.top_level_category = Category.objects.create(
            name=self.top_level_category_name
        )
        self.first_sibling_category = Category.objects.create(
            name=self.first_sibling_category_name,
            parent=self.top_level_category
        )
        self.second_sibling_category = Category.objects.create(
            parent=self.top_level_category,
            name=self.second_sibling_category_name
        )

    @staticmethod
    def test_uuids():
        """
        The test fails if an exception caused by the uuid repetition
        is raised.
        """
        for i in range(3):
            Category.objects.create(name=fake.text(15))

    def test_serialization(self):
        expected_serialization = f"<{self.top_level_category.name}>"
        self.assertEqual(expected_serialization,
                         str(self.top_level_category))

    def test_parent_reference(self):
        """
        Self-referencing hierarchical categories: siblings reference parent.
        """
        self.assertEqual(self.first_sibling_category.parent.name,
                         self.top_level_category_name)
        self.assertEqual(self.second_sibling_category.parent.name,
                         self.top_level_category_name)

    def test_subcategories_reference(self):
        """
        Self-referencing hierarchical categories: parent references
        sub-categories
        """
        number_of_sub_categories = 2
        subcategory_1 = str(self.first_sibling_category)
        subcategory_2 = str(self.second_sibling_category)
        subcategories_from_parent = [
            str(subcategory) for subcategory
            in self.top_level_category.sub_categories.all()]

        self.assertEqual(self.top_level_category.sub_categories.count(),
                         number_of_sub_categories)
        self.assertIn(subcategory_1, subcategories_from_parent)
        self.assertIn(subcategory_2, subcategories_from_parent)

    def test_deleting_empty_subcategory(self):
        self.top_level_category.sub_categories.all().delete()

        self.assertRaises(
            ObjectDoesNotExist,
            lambda: self.get_category(self.first_sibling_category_name))
        self.assertFalse(self.top_level_category.sub_categories.all())

    def test_deleting_non_empty_top_category(self):
        self.assertRaises(ProtectedError,
                          self.top_level_category.delete)

    def test_emptying_and_deleting(self):
        """
        Test deleting top category after clearing subcategories.
        """
        self.top_level_category.sub_categories.set([])
        self.top_level_category.save()

        self.assertTrue(self.top_level_category.delete())
        self.assertTrue(
            all([self.get_category(self.first_sibling_category_name),
                 self.get_category(self.second_sibling_category_name)]))

    def test_duplicate_category(self):
        """
        Attempt to add same-named sibling category.
        """
        new_category = Category(name=self.first_sibling_category_name)
        new_category.save()

        def duplicate_category():
            self.top_level_category.sub_categories.add(new_category)
            self.top_level_category.save()

        self.assertRaises(IntegrityError, duplicate_category)

    @staticmethod
    def get_category(name: str):
        return Category.objects.get(name=name)


class CategoryJoins(TestCase):
    @classmethod
    def setUp(self):
        self.user = fake_data_objects.make_fake_user()

    def tearDown(self):
        self.user.delete()

    def test_user_categories(self):
        parent_category = Category.objects.create(name="Parent category")
        subcategory = Category.objects.create(
            name="first subcategory",
            parent=parent_category
        )
        self.user.selected_categories.add(subcategory)
        self.user.save()

        self.assertEqual(subcategory.category_users.first().username,
                         self.user.username)
        self.assertEqual(self.user.selected_categories.first().name,
                         subcategory.name)

    def test_ignored_cards(self):
        # TODO: should go elsewhere
        card = fake_data_objects.make_fake_card()
        self.user.ignored_cards.add(card)

        self.assertEqual(self.user.ignored_cards.first(), card)
        self.assertEqual(card.ignoring_users.first(), self.user)


class CardSingleCategory(TestCase):
    @classmethod
    def setUpTestData(cls):
        category_name_len = 20
        cls.category_name = fake.text(category_name_len)

    def setUp(self):
        self.card = self.make_card_with_category(self.category_name)
        self.category = self.card.categories.first()

    def tearDown(self):
        self.category.id and self.category.delete()
        self.card.id and self.card.delete()

    def test_card_category(self):
        expected_number_of_categories = 1
        received_number_of_categories = len(self.card.categories.all())
        self.assertEqual(received_number_of_categories,
                         expected_number_of_categories)
        self.assertEqual(self.card.categories.first().name, self.category_name)

    def test_deleting_category_keeps_card(self):
        self.category.delete()
        self.card.refresh_from_db()
        self.assertTrue(self.card.id)

    def test_deleting_card_keeps_category(self):
        self.card.delete()
        self.category.refresh_from_db()
        self.assertFalse(self.card.id)
        self.assertTrue(self.category.id)

    def test_clearing_categories(self):
        """
        Clearing card categories shouldn't cause a category to be removed.
        """
        self.card.categories.set([])
        self.category.refresh_from_db()
        self.assertTrue(self.category.id)

    @staticmethod
    def make_card_with_category(category_name=fake.text(20)):
        card = fake_data_objects.make_fake_card()
        category = fake_data_objects.make_fake_category(category_name)
        card.categories.add(category)
        return card


class CardMultipleCategories(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.setup_categories()
        cls.setup_cards()

    @classmethod
    def setup_categories(cls):
        cls.category_names_card_1 = cls.make_category_names()
        cls.category_names_card_2 = cls.make_category_names()
        cls.card_1_categories = cls.make_categories(cls.category_names_card_1)
        cls.card_2_categories = cls.make_categories(cls.category_names_card_2)

    @classmethod
    def setup_cards(cls):
        number_of_cards = 2
        cls.card_1, cls.card_2 = fake_data_objects.make_fake_cards(
            number_of_cards)
        cls.card_1.categories.set(cls.card_1_categories)
        cls.card_2.categories.set(cls.card_2_categories)

    @staticmethod
    def make_categories(category_names: List[str]):
        return [fake_data_objects.make_fake_category(name)
                for name in category_names]

    @staticmethod
    def make_category_names():
        # number for a single card, 4 in total (for the whole class)
        card_number_of_categories = range(2)
        category_name_len = 20

        return [fake.text(category_name_len)
                for _ in card_number_of_categories]

    def test_number_of_categories(self):
        """
        Each card is assigned to 2 categories.
        """
        expected_number_of_categories = 2  # for each card
        received_number_of_categories_c1 = self.card_1.categories.count()
        received_number_of_categories_c2 = self.card_2.categories.count()

        self.assertEqual(expected_number_of_categories,
                         received_number_of_categories_c1)
        self.assertEqual(expected_number_of_categories,
                         received_number_of_categories_c2)

    def test_proper_categories_card1(self):
        expected_categories = set(self.card_1_categories)
        received_categories = set(self.card_1.categories.all())
        self.assertSetEqual(expected_categories, received_categories)

    def test_proper_categories_card2(self):
        expected_categories = set(self.card_2_categories)
        received_categories = set(self.card_2.categories.all())
        self.assertSetEqual(expected_categories, received_categories)