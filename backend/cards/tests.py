import django.db.utils
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from .models import Card, Template, Category
from faker import Faker

fake = Faker()


# Create your tests here.
class TemplateModelTests(TestCase):
    def setUp(self):
        self.template_title = fake.text(60)
        self.description = fake.text(300)
        self.body = fake.text(300)

        self.template = Template.objects.create(
            title=self.template_title,
            description=self.description,
            body=self.body
        )

    def test_duplicate_template(self):
        def duplicate_template():
            template = Template.objects.create(
                title=self.template_title,
                description=self.description,
                body=self.body
            )
            template.save()
        self.assertRaises(django.db.utils.IntegrityError, duplicate_template)

    def test_uuids(self):
        """Check if constructor doesn't duplicate uuids, which could happen
        if function for creating uuid is passed wrong: ie
        value returned from the function is passed instead
        of a callable function object.
        """
        for i in range(3):
            Template.objects.create(
                title=fake.text(15),
                description=fake.text(20),
                body=fake.text(20)
            )

    def test_last_modified_update(self):
        """Test if last_modified attribute changes when modified.
        """
        prev_last_modified = self.template.last_modified
        self.template.front = "New test card's question."
        self.template.save()

        self.assertNotEqual(self.template.last_modified, prev_last_modified)

    def test_serialization(self):
        expected_serialization = f"<{self.template_title}>"
        actual_serialization = str(self.template)
        self.assertEqual(actual_serialization, expected_serialization)


class CardModelTests(TestCase):
    def setUp(self):
        self.front = "Test card's question."
        self.back = "Test card's answer."

        self.card = Card.objects.create(
            front=self.front,
            back=self.back
        )

    def test_duplicate_card(self):
        def duplicate_card():
            card = Card.objects.create(
                front=self.front,
                back=self.back
            )
        self.assertRaises(django.db.utils.IntegrityError, duplicate_card)

    def test_uuids(self):
        for i in range(3):
            Template.objects.create(
                title=fake.text(15),
                description=fake.text(20),
                body=fake.text(20)
            )

    def test_last_modified_update(self):
        """Test if last_modified attribute changes when modified.
        """
        prev_last_modified = self.card.last_modified
        self.card.front = "New test card's question."
        self.card.save()

        self.assertNotEqual(self.card.last_modified, prev_last_modified)

    def test_serialization(self):
        expected_serialization = ("Q: Test card's question.; A: Test card's"
                                  + " answer.")
        actual_serialization = str(self.card)
        self.assertEqual(actual_serialization, expected_serialization)


class TemplateCardRelationshipTests(TemplateModelTests, CardModelTests):
    def setUp(self):
        TemplateModelTests.setUp(self)
        CardModelTests.setUp(self)
        card = Card.objects.first()
        card.template = Template.objects.first()
        card.save()

    def test_add_template_to_card(self):
        card, template = self._get_tested_objects()
        card.template = template
        card.save()

        self.assertTrue(card.template is template)
        self.assertTrue(card.template_id == template.id)

    def test_card_related_name(self):
        card, template = self._get_tested_objects()
        card_from_template = template.cards.first()

        self.assertEqual(card_from_template.front, card.front)

    def _get_tested_objects(self):
        card = Card.objects.first()
        template = Template.objects.first()

        return card, template

    def test_remove_template_from_card(self):
        card, template = self._get_tested_objects()
        card.template = None
        card.save()

        self.assertFalse(card.template is template)
        self.assertTrue(Template.objects.get(title=self.template_title))
        self.assertFalse(card.template)
        self.assertFalse(card.template_id == template.id)

    def test_removing_template(self):
        card, template = self._get_tested_objects()

        self.assertRaises(ProtectedError, template.delete)

        # remove reference to the template and delete it:
        card.template = None
        card.save()
        template.delete()

        self.assertRaises(
            ObjectDoesNotExist,
            lambda: Template.objects.get(title=self.template_title))


class CategoryTests(TestCase):
    def setUp(self):
        CATEGORY_NAME_LEN = 20
        self.first_category_name = fake.text(CATEGORY_NAME_LEN)
        self.second_category_name = fake.text(CATEGORY_NAME_LEN)
        self.third_category_name = fake.text(CATEGORY_NAME_LEN)

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
        NUMBER_OF_SUB_CATEGORIES = 2
        first_category = self.get_category(self.first_category_name)
        second_category = self.get_category(self.second_category_name)

        self.assertEqual(len(first_category.sub_categories.all()),
                         NUMBER_OF_SUB_CATEGORIES)
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
        self.assertRaises(django.db.utils.IntegrityError, duplicate_category)

    @staticmethod
    def get_category(name: str):
        return Category.objects.get(name=name)
