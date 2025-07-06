import django.db.utils
from django.test import TestCase
from faker import Faker
from cards.models import CardTemplate


fake = Faker()


class TemplateModelTests(TestCase):
    def setUp(self):
        self.template_title = fake.text(60)
        self.description = fake.text(300)
        self.body = fake.text(300)

        self.template = CardTemplate.objects.create(
            title=self.template_title,
            description=self.description,
            body=self.body
        )

    def test_duplicate_template(self):
        def duplicate_template():
            template = CardTemplate.objects.create(
                title=self.template_title,
                description=self.description,
                body=self.body
            )
            template.save()

        self.assertRaises(django.db.utils.IntegrityError, duplicate_template)

    @staticmethod
    def test_uuids():
        """Check if constructor doesn't duplicate uuids, which could happen
        if function for creating uuid is passed wrong: ie
        value returned from the function is passed instead
        of a callable function object.
        """
        for i in range(3):
            CardTemplate.objects.create(
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
