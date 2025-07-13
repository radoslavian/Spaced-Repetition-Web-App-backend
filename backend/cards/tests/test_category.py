from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.deletion import ProtectedError
from django.db.utils import IntegrityError
from django.test import TestCase
from cards.models import Card, Category
from cards.tests.fake_data import fake


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
    def test_user_categories(self):
        user_model = get_user_model()
        username = fake.profile()["username"]
        user = user_model.objects.create_user(username=username)
        parent_category = Category(name="Parent category")
        first_subcategory = Category(
            name="first subcategory",
            parent=parent_category
        )
        parent_category.save()
        first_subcategory.save()
        user.selected_categories.add(first_subcategory)
        user.save()

        self.assertEqual(first_subcategory.category_users.first().username,
                         user.username)
        self.assertEqual(user.selected_categories.first().name,
                         first_subcategory.name)

    def test_ignored_cards(self):
        user_model = get_user_model()
        user = user_model(username=fake.text(6))
        user.save()
        card = Card(
            front=fake.text(100),
            back=fake.text(100)
        )
        card.save()
        user.ignored_cards.add(card)

        self.assertEqual(user.ignored_cards.first().front,
                         card.front)
        self.assertEqual(card.ignoring_users.first().username,
                         user.username)
