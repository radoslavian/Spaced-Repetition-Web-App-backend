from django.core.exceptions import ObjectDoesNotExist
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from .models import Card, Template, Category
import hashlib
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

    def test_uuids(self):
        """Check if doesn't duplicate uuids, which could happen
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
    def test_template_hashing(self):
        template_hash = hashlib.sha256(
            bytes(self.template_title + self.description + self.body, "utf-8")
        ).hexdigest()
        self.assertEqual(template_hash, self.template.hash)

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

    def test_uuids(self):
        for i in range(3):
            Template.objects.create(
                title=fake.text(15),
                description=fake.text(20),
                body=fake.text(20)
            )

    def test_new_card_hashing(self):
        card_hash = hashlib.sha256(
            bytes(self.front + self.back, "utf-8")).hexdigest()
        self.assertEqual(card_hash, self.card.hash)

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
            Category.objects.create(
                name=fake.text(15),
            )

    def test_serialization(self):
        category = Category.objects.first()
        expected_serialization = f"<{category.name}>"

        self.assertEqual(expected_serialization, str(category))

    def test_self_reference(self):
        NUMBER_OF_SUB_CATEGORIES = 2
        first_category = Category.objects.get(name=self.first_category_name)
        second_category = Category.objects.get(name=self.second_category_name)

        self.assertEqual(len(first_category.sub_categories.all()),
                         NUMBER_OF_SUB_CATEGORIES)
        self.assertEqual(second_category.parent.name,
                         self.first_category_name)

    def test_deleting_categories(self):
        # model should allow for deleting categories with subcategories
        # check if deleting subcategory doesn't remove parent category
        pass

    def test_same_named_categories(self):
        # two cat. with the same name and with the same parent category
        # ... with different parent category
        pass
