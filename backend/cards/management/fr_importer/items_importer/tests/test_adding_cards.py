import uuid

from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist

from cards.management.fr_importer.items_importer.modules.imported_card import \
    ImportedCard
from cards.management.fr_importer.items_parser.modules.html_formatted_card import \
    HtmlFormattedCard
from cards.models import Card, CardTemplate


class AddingBasicCard(TestCase):
    """
    Adding a card (no template, no files) - just a question and answer.
    """
    @classmethod
    def setUpTestData(cls):
        question = "card question"
        answer = "card answer"
        cls.formatted_card = HtmlFormattedCard({"question": question,
                                                "answer": answer})
        cls.imported_card = ImportedCard(cls.formatted_card)
        cls.imported_card.save()
        cls.queried_cards = Card.objects.all()
        cls.queried_card = Card.objects.first()

    def test_one_card_created(self):
        self.assertEqual(len(self.queried_cards), 1)

    def test_question(self):
        self.assertEqual(self.formatted_card.question_output_text,
                         self.queried_card.front)

    def test_answer(self):
        self.assertEqual(self.formatted_card.answer_output_text,
                         self.queried_card.back)

    def test_no_sound_files(self):
        self.assertFalse(self.queried_card.front_audio)
        self.assertFalse(self.queried_card.back_audio)

    def test_no_images(self):
        self.assertFalse(self.queried_card.front_images)
        self.assertFalse(self.queried_card.back_images)


class SettingTemplate(TestCase):
    def setUp(self):
        self.formatted_card = HtmlFormattedCard(
            {"question": "q", "answer": "a"})
        self.imported_card = ImportedCard(self.formatted_card)
        self.imported_card.save()
        self.template = CardTemplate()
        self.template.save()

    def test_add_template(self):
        """
        Adding template to the card.
        """
        self.imported_card.set_template(self.template)
        card = Card.objects.first()
        self.assertEqual(card.template_id, self.template.id)

    def test_add_template_by_uuid(self):
        template_uuid = self.template.id
        self.imported_card.set_template_by_uuid(template_uuid)
        card = Card.objects.first()
        self.assertEqual(card.template_id, template_uuid)

    def test_add_template_by_uuid_string(self):
        template_uuid_string = str(self.template.id)
        self.imported_card.set_template_by_uuid(template_uuid_string)
        card = Card.objects.first()
        self.assertEqual(card.template_id, self.template.id)

    def test_raises_wrong_template_uuid(self):
        """
        Should raise exception if template was not found.
        """
        template_uuid = uuid.uuid4()
        raise_error = lambda: (
            self.imported_card.set_template_by_uuid(template_uuid))
        self.assertRaises(ObjectDoesNotExist, raise_error)
