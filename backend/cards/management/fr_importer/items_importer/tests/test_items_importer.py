import datetime
from unittest import skip

from django.contrib.auth import get_user_model
from django.core.exceptions import MultipleObjectsReturned
from django.test import TestCase
from faker import Faker

from cards.management.fr_importer.items_importer.modules.items_importer import \
    PendingItemsImporter, MemorizedItemsImporter
from cards.management.fr_importer.items_parser.items_parser import ItemsParser
from cards.management.fr_importer.items_parser.modules.html_formatted_card import \
    HtmlFormattedCard
from cards.management.fr_importer.items_parser.modules.user_review import \
    UserReview
from cards.models import Category, Card, CardTemplate, CardUserData


class ItemsImporterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.fake = Faker()

        cls.category_1_name = "category 1"
        cls.category_2_name = "category 2"
        category_1 = Category(name=cls.category_1_name)
        category_2 = Category(name=cls.category_2_name)
        category_1.save()
        category_2.save()
        cls.categories = [category_1, category_2]

        cls.template_title = "card template"
        cls.template_description = "test template"
        cls.template_body = cls.fake.text(100)
        cls.template = CardTemplate(
            title=cls.template_title,
            description=cls.template_description,
            body=cls.template_body
        )
        cls.template.save()

        cls.elements_path = ("cards/management/fr_importer/items_importer/"
                             "tests/test_data/fdb/elements.xml")

    def setUp(self):
        self.items_importer = PendingItemsImporter(self.elements_path)

    def test_number_of_cards(self):
        """
        Number of cards created in the database.
        """
        self.items_importer.import_cards_into_db()
        expected_number = 3
        received_number = Card.objects.count()
        self.assertEqual(expected_number, received_number)

    def test_cards_imported(self):
        """
        Three unique cards should be imported into db.
        """
        self.items_importer.import_cards_into_db()
        # for brevity, we compare card's fronts/questions only
        expected_card_questions = {card.question_output_text
                                   for card in ItemsParser(self.elements_path)}
        cards_from_db = Card.objects.all()
        received_card_questions = {card.front for card in cards_from_db}
        self.assertSetEqual(expected_card_questions, received_card_questions)

    def test_adding_cards_to_category(self):
        """
        All cards should be added to one but not the other category.
        """
        # the .name == "category 1" == cls.category_1_name
        categories = [self.categories[0].id]
        self.items_importer.set_categories(categories)
        self.items_importer.import_cards_into_db()

        cards = Card.objects.all()
        expected_number_of_categories = 1

        # otherwise the test will pass, even if there are no cards
        self.assertTrue(cards)

        for card in cards:
            self.assertEqual(len(card.categories.all()),
                             expected_number_of_categories)
            card_categories = card.categories.all()
            self.assertEqual(card_categories[0].name,
                             self.category_1_name)

    def test_adding_template(self):
        """
        Each card is given the same template.
        """
        self.items_importer.set_template(self.template)
        self.items_importer.import_cards_into_db()
        self.assert_template_title()

    def test_adding_template_by_uuid(self):
        self.items_importer.set_template_by_uuid(self.template.id)
        self.items_importer.import_cards_into_db()
        self.assert_template_title()

    def test_adding_templated_by_title(self):
        self.items_importer.set_template_by_title(self.template_title)
        self.items_importer.import_cards_into_db()
        self.assert_template_title()

    def assert_template_title(self):
        """
        A shortcut for tests of setting cards' template:
        * test_adding_template
        * test_adding_template_by_uuid
        * test_adding_templated_by_title
        """
        cards = Card.objects.all()

        # otherwise tests will pass, even if there are no cards
        self.assertTrue(cards)

        for card in cards:
            self.assertEqual(card.template.title,
                             self.template.title)

    def test_adding_template_by_title_error(self):
        """
        Should raise error if there are several templates with the same title.
        """
        second_template = CardTemplate(
            title=self.template_title,
            description=self.fake.text(200),
            body=self.fake.text(100)
        )
        second_template.save()
        expected_error_message = ("get() returned more than one"
                                  " CardTemplate -- it returned 2!")

        with self.assertRaisesMessage(MultipleObjectsReturned,
                                      expected_error_message):
            self.items_importer.set_template_by_title(self.template_title)

    def test_card_multiple_categories(self):
        # one by id, another by Category object
        categories = [self.categories[0].id, self.categories[1]]
        self.items_importer.set_categories(categories)
        self.items_importer.import_cards_into_db()

        cards = Card.objects.all()
        expected_number_of_categories = 2

        # otherwise the test will pass, even if there are no cards
        self.assertTrue(cards)

        for category in self.categories:
            for card in cards:
                self.assertTrue(card.categories)
                self.assertEqual(len(card.categories.all()),
                                 expected_number_of_categories)
                card_categories_names = [
                    card_category.name
                    for card_category in card.categories.all()]
                self.assertIn(category.name, card_categories_names)

    def test_selecting_category_to_import(self):
        """
        Should import cards only from selected category.
        """
        import_category = "category_1.category_2.category 3"
        self.items_importer.set_import_category(import_category)
        self.items_importer.import_cards_into_db()
        self.assert_cards_from_categories()

    def test_selecting_category_to_import_by_xpath(self):
        """
        Should import cards only from categories selected by a xpath.
        """
        import_category = ("./category[@name='category_1']"
                           "/category[@name='category_2']"
                           "/category[@name='category 3']")
        self.items_importer.set_import_category_xpath(import_category)
        self.items_importer.import_cards_into_db()
        self.assert_cards_from_categories()

    def assert_cards_from_categories(self):
        """
        A shortcut for tests:
        * test_selecting_category_to_import
        * test_selecting_category_to_import_by_xpath
        It will only work if both tests import cards from the same category.
        """
        cards = Card.objects.all()
        card = HtmlFormattedCard({"question": "question 3",
                                  "answer": "answer 3"})
        expected_question_value = card.question_output_text
        expected_answer_value = card.answer_output_text
        expected_number_of_cards = 1
        received_number_of_cards = len(cards)
        received_card = cards.first()
        self.assertEqual(received_number_of_cards, expected_number_of_cards)
        self.assertEqual(received_card.front, expected_question_value)
        self.assertEqual(received_card.back, expected_answer_value)


class MemorizedItemsImporterTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User(username="user")
        cls.user.save()
        review_data = dict(id="1234800390",
                           tmtrpt="7440",
                           stmtrpt="7440",
                           livl="1099",
                           rllivl="1646",
                           ivl="1551",
                           rp="14",
                           gr="5")
        cls.user_review = UserReview(review_data, time_of_start="1186655166")
        cls.elements_path = ("cards/management/fr_importer/items_importer/"
                             "tests/test_data/fdb/elements.xml")
        cls.import_category_path = "category_1.category_2.category 3"

    def setUp(self):
        self.card_importer = MemorizedItemsImporter(self.elements_path,
                                                    user=self.user)
        self.card_importer.set_import_category(self.import_category_path)

    def test_card_user_review(self):
        """
        Should create CardUserData instance for a given user and card.
        """
        self.card_importer.import_cards_into_db()
        card = Card.objects.first()
        review_data = CardUserData.objects.get(card=card, user=self.user)
        introduced_on = datetime.datetime(2009, 2, 16, 16, 6, 30,
                                          tzinfo=datetime.timezone.utc)
        dict_user_review = {**dict(self.user_review),
                            "last_reviewed": datetime.date(2023, 9, 23),
                            "introduced_on": introduced_on,
                            'review_date': datetime.date(2027, 12, 22)}
        self.assertDictEqual(dict_user_review, dict(review_data))
