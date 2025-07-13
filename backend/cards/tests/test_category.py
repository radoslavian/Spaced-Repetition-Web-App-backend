from django.core.exceptions import ObjectDoesNotExist
from django.db.models.deletion import ProtectedError
from django.db.utils import IntegrityError
from django.test import TestCase
from cards.models import Category
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
        """Test deleting top category after clearing subcategories.
        """
        first_category = self.get_category(self.top_level_category_name)
        first_category.sub_categories.set([])
        first_category.save()

        self.assertTrue(first_category.delete())
        self.assertTrue(
            all([self.get_category(self.first_sibling_category_name),
                 self.get_category(self.second_sibling_category_name)]))

    def test_duplicate_category(self):
        """Attempt to add same-named sibling category.
        """
        parent_category = self.get_category(self.top_level_category_name)
        new_category = Category(name=self.first_sibling_category_name)
        new_category.save()

        def duplicate_category():
            parent_category.sub_categories.add(new_category)
            parent_category.save()

        self.assertRaises(IntegrityError, duplicate_category)

    @staticmethod
    def get_category(name: str):
        return Category.objects.get(name=name)