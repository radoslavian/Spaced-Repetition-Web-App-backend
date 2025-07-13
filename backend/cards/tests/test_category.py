from django.core.exceptions import ObjectDoesNotExist
from django.db.models.deletion import ProtectedError
from django.db.utils import IntegrityError
from django.test import TestCase
from faker import Faker
from cards.models import Category


fake = Faker()


class CategoryTests(TestCase):
    def setUp(self):
        category_name_len = 20
        self.first_category_name = fake.text(category_name_len)
        self.second_category_name = fake.text(category_name_len)
        self.third_category_name = fake.text(category_name_len)

        first_category = Category.objects.create(
            name=self.first_category_name
        )
        Category.objects.create(
            name=self.second_category_name,
            parent=first_category
        )
        Category.objects.create(
            parent=first_category,
            name=self.third_category_name
        )

    @staticmethod
    def test_uuids():
        for i in range(3):
            Category.objects.create(name=fake.text(15))

    def test_serialization(self):
        category = Category.objects.first()
        expected_serialization = f"<{category.name}>"

        self.assertEqual(expected_serialization, str(category))

    def test_self_reference(self):
        number_of_sub_categories = 2
        first_category = self.get_category(self.first_category_name)
        second_category = self.get_category(self.second_category_name)

        self.assertEqual(first_category.sub_categories.count(),
                         number_of_sub_categories)
        self.assertEqual(second_category.parent.name,
                         self.first_category_name)

    def test_deleting_empty_subcategory(self):
        first_category = self.get_category(self.first_category_name)
        for sub_category in first_category.sub_categories.all():
            sub_category.delete()

        self.assertRaises(
            ObjectDoesNotExist,
            lambda: self.get_category(self.second_category_name))

        # as stated in the documentation, treebeard relies on raw
        # SQL expressions to manage model, so after applying changes model
        # requires re-fetch from the database in order to stay up-to-date
        self.assertTrue(self.get_category(self.first_category_name))

    def test_deleting_non_empty_top_category(self):
        first_category = self.get_category(self.first_category_name)

        self.assertRaises(ProtectedError, first_category.delete)

    def test_emptying_and_deleting(self):
        """Test deleting top category after clearing subcategories.
        """
        first_category = self.get_category(self.first_category_name)
        first_category.sub_categories.set([])
        first_category.save()

        self.assertTrue(first_category.delete())
        self.assertTrue(all([self.get_category(self.second_category_name),
                             self.get_category(self.third_category_name)]))

    def test_duplicate_category(self):
        """Attempt to add same-named sibling category.
        """
        parent_category = self.get_category(self.first_category_name)
        new_category = Category(name=self.second_category_name)
        new_category.save()

        def duplicate_category():
            parent_category.sub_categories.add(new_category)
            parent_category.save()

        self.assertRaises(IntegrityError, duplicate_category)

    @staticmethod
    def get_category(name: str):
        return Category.objects.get(name=name)