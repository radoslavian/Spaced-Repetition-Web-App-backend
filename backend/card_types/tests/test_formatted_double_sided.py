"""
The description for text fields should contain unmarked text.
The markup should be added in a separate template.
"""
from django.test import TestCase

from card_types.models import CardNote
from cards.models import CardTemplate


class RenderingDoubleSided(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.card_description = {
            "_front": {
                "text": "some front text"
            },
            "_back": {
                "text": "some back text"
            }
        }

    @classmethod
    def setup_objects(cls):
        cls.note = CardNote.objects.create(
            card_description=cls.card_description,
            card_type="double-sided-formatted")
        cls.front_back_card = cls.note.cards.get(
            id__exact=cls.note.metadata["front-back-card-id"])


class DefaultClassTemplate(RenderingDoubleSided):
    """
    Card sides can be rendered using the default template string.
    The default... is embedded in the card/note manager class.
    """
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.setup_objects()

    def test_front_side(self):
        expected_text = f"<h3>{self.card_description['_front']['text']}</h3>"
        self.assertEqual(expected_text, self.front_back_card.front)

    def test_back_side(self):
        expected_text = f"<h3>{self.card_description['_back']['text']}</h3>"
        self.assertEqual(expected_text, self.front_back_card.back)


class TemplateString(RenderingDoubleSided):
    """
    Rendering card sides using a template string from the description.
    Card sides can be rendered using a formatting template string embedded
    in the card description (CardNote.card_description field).
    """
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.card_description = {**cls.card_description,
                                "formatting_template_string": (
                                    "<p id='formatting-string'>"
                                    "{{ side.text|safe }}</p>")}
        cls.setup_objects()

    def test_front(self):
        expected = ("<p id='formatting-string'>"
                     f"{self.card_description['_front']['text']}</p>")
        self.assertEqual(expected, self.front_back_card.front)

    def test_back(self):
        expected = ("<p id='formatting-string'>"
                    f"{self.card_description['_back']['text']}</p>")
        self.assertEqual(expected, self.front_back_card.back)


class DatabaseTemplate(RenderingDoubleSided):
    """
    Rendering card sides using a database template fetched by its name.
    """
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        body = "<p id='db-template-formatting-string'>{{ side.text|safe }}</p>"
        db_template_name = "database_template"
        cls.db_template = CardTemplate.objects.create(
            title=db_template_name,
            body=body,
            description="test formatting template")
        cls.card_description = {**cls.card_description,
                                "formatting_template_db": db_template_name}
        cls.setup_objects()

    def test_front(self):
        expected = ("<p id='db-template-formatting-string'>"
                    f"{self.card_description['_front']['text']}</p>")
        self.assertEqual(expected, self.front_back_card.front)

    def test_back(self):
        expected = ("<p id='db-template-formatting-string'>"
                    f"{self.card_description['_back']['text']}</p>")
        self.assertEqual(expected, self.front_back_card.back)


class CardTemplateByName(RenderingDoubleSided):
    """
    Fetching a card template by its title rather than uuid.
    Getting a template by name looks cleaner and is more human-readable,
    though it may fail unexpectedly if the name is changed.
    Card template - is referenced in card.template and is responsible for
    rendering a card to a user (not to be confused with card-side formatting
    template, used in card notes).
    """
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.expected_text = "expected text"
        cls._create_objects()

    @classmethod
    def _create_objects(cls):
        template_title = "named template"
        card_type = "double-sided-formatted"
        cls.template = CardTemplate.objects.create(title=template_title,
                                                   body=cls.expected_text)
        cls.card_description = {**cls.card_description,
                                "formatting_template_db": None,
                                "template_title": template_title}
        cls.note = CardNote.objects.create(
            card_description=cls.card_description,
            card_type=card_type)

    def test_card_template_by_name(self):
        front_back_card = self.note.cards.get(
            id=self.note.metadata["front-back-card-id"])
        back_front_card = self.note.cards.get(
            id=self.note.metadata["back-front-card-id"])

        self.assertIn(self.expected_text, front_back_card.render({}))
        self.assertIn(self.expected_text, back_front_card.render({}))