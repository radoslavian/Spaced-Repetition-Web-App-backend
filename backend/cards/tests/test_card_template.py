import django.db.utils
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from lxml.html.defs import top_level_tags

from cards.models import Card, CardTemplate
from cards.tests.fake_data import fake_data_objects


class CreatingTemplate(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.template_data = fake_data_objects.get_fake_template_data()

    def setUp(self):
        self.template = CardTemplate.objects.create(**self.template_data)

    def test_template_duplication(self):
        def duplicate_template():
            template = CardTemplate.objects.create(**self.template_data)
            template.save()

        self.assertRaises(django.db.utils.IntegrityError, duplicate_template)

    @staticmethod
    def test_uuids():
        """
        Raises exception if uuid is added incorrectly (passes otherwise).
        """
        for i in range(3):
            str_i = str(i)
            CardTemplate.objects.create(
                title="title " + str_i,
                description="description " + str_i,
                body="body " + str_i
            )

    def test_last_modified_update(self):
        """
        The last_modified attribute should get updated if template is modified.
        """
        prev_last_modified = self.template.last_modified
        self.template.body = "New test templates's body."
        self.template.save()

        self.assertNotEqual(self.template.last_modified, prev_last_modified)

    def test_serialization(self):
        expected_serialization = f"<{self.template_data['title']}>"
        actual_serialization = str(self.template)
        self.assertEqual(actual_serialization, expected_serialization)


class TemplateCardRelationship(TestCase):
    """
    Linking CardTemplate to a Card instance.
    """

    @classmethod
    def setUpTestData(cls):
        cls.card_data = fake_data_objects.get_fake_card_data()
        cls.template_data = fake_data_objects.get_fake_template_data()

    def setUp(self):
        self.template = CardTemplate.objects.create(**self.template_data)
        self.card = Card.objects.create(**self.card_data,
                                        template=self.template)

    def test_add_template_to_card(self):
        self.card.template = self.template
        self.card.save()

        self.assertTrue(self.card.template is self.template)
        self.assertTrue(self.card.template_id == self.template.id)

    def test_card_related_name(self):
        card_from_template = self.template.cards.first()
        self.assertEqual(card_from_template.front, self.card.front)

    def test_remove_template_from_card(self):
        self.card.template = None
        template_title = self.template_data["title"]
        self.card.save()

        self.assertFalse(self.card.template is self.template)
        self.assertFalse(self.card.template)
        self.assertFalse(self.card.template_id == self.template.id)
        self.assertTrue(CardTemplate.objects.get(title=template_title))

    def test_deleting_template_linked_to_card(self):
        """
        An attempt to remove a template linked to a card.
        """
        self.assertRaises(ProtectedError, self.template.delete)

    def test_deleting_unlinked_template(self):
        """
        Removing template unlinked from a card.
        """
        template_title = self.template_data["title"]
        self.card.template = None
        self.card.save()
        self.template.delete()

        self.assertRaises(
            ObjectDoesNotExist,
            lambda: CardTemplate.objects.get(title=template_title))


class DatabaseTemplateImport(TestCase):
    """
    Including a database template into another one using a custom template
    loader.
    """
    @classmethod
    def setUpTestData(cls):
        cls.top_level_template_title = "top-level template"
        cls.partial_template_title = "partial template"
        cls.top_level_template_src = f"""
        <!-- {cls.top_level_template_title} -->"
        {{% include "{cls.partial_template_title}" %}}  
        """
        cls.partial_template_src = (f"<!-- {cls.partial_template_title} -->\n"
                                    '<p id="card-front">{{ card.front }}</p>\n'
                                    '<p id="card-back">{{ card.back }}</p>')

        cls.top_level_template = CardTemplate.objects.create(
            title=cls.top_level_template_title,
            body=cls.top_level_template_src)
        cls.partial_template = CardTemplate.objects.create(
            title=cls.partial_template_title,
            body=cls.partial_template_src)

        cls.card_front = "card front"
        cls.card_back = "card back"
        cls.card = Card.objects.create(front=cls.card_front,
                                       back=cls.card_back,
                                       template=cls.top_level_template)
        cls.card_rendering = cls.card.render({})

    def test_full_template_rendered(self):
        self.assertIn(self.top_level_template_title, self.card_rendering)

    def test_partial_template_rendered(self):
        self.assertIn(self.partial_template_title, self.card_rendering)
        self.assertIn(self.card_front, self.card_rendering)
        self.assertIn(self.card_back, self.card_rendering)