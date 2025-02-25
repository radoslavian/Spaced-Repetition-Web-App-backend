from django.test import TestCase

from cards.management.fr_importer.items_importer.modules.imported_card import \
    ImportedCard
from cards.management.fr_importer.items_parser.modules.html_formatted_card import \
    HtmlFormattedCard
from cards.models import Card, CardTemplate


class AddingBasicCard(TestCase):
    """
    Adding a card (no template, no files) - just a question and answer.
    """
    def setUp(self):
        question = "card question"
        answer = "card answer"
        self.formatted_card = HtmlFormattedCard({"question": question,
                                                "answer": answer})
        self.imported_card = ImportedCard(self.formatted_card)
        self.imported_card.save()
        self.queried_cards = Card.objects.all()
        self.queried_card = Card.objects.first()

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

    def test_add_template(self):
        """
        Adding template to the card.
        """
        template = CardTemplate()
        template.save()
        self.imported_card.set_template(template)
        self.queried_card.refresh_from_db()

        self.assertEqual(self.queried_card.template_id, template.id)
