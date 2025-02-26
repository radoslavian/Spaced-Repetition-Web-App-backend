import uuid

from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist

from cards.management.fr_importer.items_importer.modules.imported_card import \
    ImportedCard
from cards.management.fr_importer.items_parser.modules.html_formatted_card import \
    HtmlFormattedCard
from cards.models import Card, CardTemplate, Category


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
        self.template_title = "very odd title of a template"
        self.template = CardTemplate(title=self.template_title)
        self.template.save()
        CardTemplate(title="another template").save()

    def test_add_template(self):
        """
        Adding template to the card.
        """
        self.imported_card.set_template(self.template)
        self.imported_card.save()
        card = Card.objects.first()
        self.assertEqual(card.template_id, self.template.id)

    def test_add_template_by_uuid(self):
        template_uuid = self.template.id
        self.imported_card.set_template_by_uuid(template_uuid)
        self.imported_card.save()
        card = Card.objects.first()
        self.assertEqual(card.template_id, template_uuid)

    def test_add_template_by_uuid_string(self):
        template_uuid_string = str(self.template.id)
        self.imported_card.set_template_by_uuid(template_uuid_string)
        self.imported_card.save()
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

    def test_add_template_by_title(self):
        """
        Adding template by template title.
        """
        self.imported_card.set_template_by_title(self.template_title)
        self.imported_card.save()
        card = Card.objects.first()
        self.assertEqual(card.template_id, self.template.id)

    def test_add_template_wrong_title(self):
        """
        Should raise exception if template (searched by a title) was not found.
        """
        raise_error = lambda: self.imported_card.set_template_by_title(
            "no title, even fake one")
        self.assertRaises(ObjectDoesNotExist, raise_error)


class SettingCategory(TestCase):
    def setUp(self):
        category_1_name = "category 1"
        category_2_name = "category 2"
        self.category_1, self.category_2, = (Category(name=category_1_name),
                                             Category(name=category_2_name))
        self.imported_card = ImportedCard(HtmlFormattedCard(
            {"question": "card question", "answer": "card answer"}))
        self.imported_card.save()
        self.category_1.save()
        self.category_2.save()

    def test_adding_single_category(self):
        category_to_add = [self.category_1]
        self.imported_card.set_categories(category_to_add)
        self.imported_card.save()
        card = Card.objects.first()

        self.assertEqual(len(category_to_add), len(card.categories.all()))
        self.assertEqual(self.category_1.id, card.categories.first().id)

    def test_adding_category_group(self):
        categories = self.category_1, self.category_2
        self.imported_card.set_categories(categories)
        self.imported_card.save()
        card = Card.objects.first()
        expected_categories_ids = {category.id for category in categories}
        card_categories_ids = {category.id
                               for category in card.categories.all()}

        self.assertEqual(len(card.categories.all()), len(categories))
        self.assertSetEqual(expected_categories_ids, card_categories_ids)

    def test_adding_category_mixed_group(self):
        """
        Adding categories by ids and objects.
        """
        group = [str(category)
                 for category in (self.category_1.id, self.category_2.id)]
        self.imported_card.set_categories(group)
        self.imported_card.save()
        card = Card.objects.first()
        card_categories_ids = {str(category.id)
                               for category in card.categories.all()}

        self.assertEqual(len(group), len(card.categories.all()))
        self.assertSetEqual(card_categories_ids, set(group))

    def test_adding_non_existing_category_by_ids(self):
        fake_category_id = uuid.uuid4()
        group_ids = [self.category_1.id, fake_category_id]
        raise_error = lambda: (
            self.imported_card.set_categories(group_ids))
        self.assertRaises(ObjectDoesNotExist, raise_error)

    def test_raises_invalid_argument(self):
        """
        Raises ValueError if incorrect argument is passed.
        """
        invalid_category = [1]
        expected_message = "Invalid argument for setting categories."
        with self.assertRaisesMessage(ValueError, expected_message):
            self.imported_card.set_categories(invalid_category)