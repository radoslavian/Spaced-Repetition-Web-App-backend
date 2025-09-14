import django.db.utils
from django.test import TestCase
from cards.models import Card, CardTemplate
from cards.tests.fake_data import fake_data_objects


class CardModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.fake_card_data = {
            "front": "Test card's question.",
            "back": "Test card's answer."
        }

    def setUp(self):
        self.card = Card.objects.create(**self.fake_card_data)

    def test_images_getter_wrong_argument(self):
        """
        The _make_images_getter should only accept 'front' or 'back'
        as a card side name.
        """
        def fail():
            side = "incorrect_side"
            self.card._make_images_getter(side)

        self.assertRaises(ValueError, fail)

    def test_duplicate_card(self):
        def duplicate_card():
            card = Card.objects.create(**self.fake_card_data)
            card.save()

        self.assertRaises(django.db.utils.IntegrityError, duplicate_card)

    def test_uuids(self):
        for i in range(3):
            str_i = str(i)
            Card.objects.create(
                front=self.fake_card_data["front"] + str_i,
                back=self.fake_card_data["back"] + str_i
            )

    def test_last_modified_update(self):
        """
        Test if last_modified attribute changes when the card is modified.
        """
        prev_last_modified = self.card.last_modified
        self.card.front = "New test card's question."
        self.card.save()

        self.assertNotEqual(self.card.last_modified, prev_last_modified)

    def test_serialization(self):
        expected_serialization = f"Card(Q: Test card's question.; " \
                                 f"A: Test card's answer.)"
        actual_serialization = str(self.card)
        self.assertEqual(actual_serialization, expected_serialization)


class CardRendering(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.template = CardTemplate.objects.create(
            title="test template",
            description="Test rendering template in database " \
                        "that extends base template.",
            body="""
                <!-- database template extending base template -->
                {% extends '_base.html' %}
                {% block content %}
                <p>{{ card.front }}</p>
                <p>{{ card.back }}</p>
                {% endblock content %}
                """
        )

    def setUp(self):
        self.card = fake_data_objects.make_fake_card()

    def tearDown(self):
        self.card.delete()

    def test_get_card_body_base_template(self):
        """get_card_body:
        test rendering template in database that extends base template.
        """
        self.card.template = self.template
        self.card.save()
        card_body = self.card.render({})

        self.assertIn("<!-- base template for cards -->", card_body)
        self.assertIn("<!-- database template extending base template -->",
                        card_body)
        self.assertIn(self.card.front, card_body)
        self.assertIn(self.card.back, card_body)

    def test_get_card_body_fallback_template(self):
        card_body = self.card.render({})

        self.assertIn("<!-- base template for cards -->", card_body)
        self.assertIn("<!-- fallback card template -->", card_body)
        self.assertIn(self.card.front, card_body)
        self.assertIn(self.card.back, card_body)