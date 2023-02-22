import uuid
from django.test import TestCase
from .models import Card, Template
import hashlib
from faker import Faker

fake = Faker()


# Create your tests here.
class TemplateModelTests(TestCase):
    def setUp(self):
        self.title = fake.text(60)
        self.description = fake.text(300)
        self.body = fake.text(300)

        self.template = Template.objects.create(
            title=self.title,
            description=self.description,
            body=self.body
        )

    def test_template_hashing(self):
        template_hash = hashlib.sha256(
            bytes(self.title + self.description + self.body, "utf-8")
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
        expected_serialization = f"<{self.title}>"
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
