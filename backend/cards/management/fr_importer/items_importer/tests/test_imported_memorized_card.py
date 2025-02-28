from django.contrib.auth import get_user_model
from django.test import TestCase

from cards.management.fr_importer.items_importer.modules.imported_memorized_card import \
    ImportedMemorizedCard
from cards.management.fr_importer.items_parser.modules.html_memorized_card import \
    HtmlFormattedMemorizedCard
from cards.management.fr_importer.items_parser.modules.user_review import \
    UserReview
from cards.models import CardUserData, Card


class AddingMemorizedCard(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User(username="user")
        cls.user.save()
        cls.time_of_start = 1186655166

        # attributes of an <item ...></item> tag
        cls.card_review_details = {
            "id": "1236435838",
            "tmtrpt": "6574",
            "stmtrpt": "6574",
            "livl": "1274",
            "rllivl": "1764",
            "ivl": "583",
            "rp": "6",
            "gr": "4"
        }
        card_data = {
            "question": "question",
            "answer": "answer",
            "review_details": cls.card_review_details
        }
        card = HtmlFormattedMemorizedCard(card_data, cls.time_of_start)
        cls.memorized_card = ImportedMemorizedCard(card, cls.user)
        cls.database_card = Card.objects.first()
        cls.database_user_review = CardUserData.objects.get(
            card=cls.database_card,
            user=cls.user)
        cls.user_review = UserReview(cls.card_review_details,
                                     cls.time_of_start)

    def test_lapses(self):
        expected_lapses = 0
        self.assertEqual(expected_lapses, self.database_user_review.lapses)

    def test_reviews(self):
        expected_reviews = 6
        self.assertEqual(expected_reviews, self.database_user_review.reviews)

    def test_total_reviews(self):
        expected_total_reviews = 6  # fr doesn't calculate tr, so tr == reviews
        self.assertEqual(expected_total_reviews,
                         self.database_user_review.total_reviews)

    def test_grade(self):
        expected_grade = 4
        self.assertEqual(expected_grade, self.database_user_review.grade)

    def test_review_date(self):
        expected_review_date = self.user_review.review_date
        received_review_date = self.database_user_review.review_date
        self.assertEqual(expected_review_date.date(), received_review_date)

    def test_introduced_on(self):
        expected_introduced_on = self.user_review.introduced_on.date()
        received_introduced_on = self.database_user_review.introduced_on.date()
        self.assertEqual(expected_introduced_on, received_introduced_on)

    def test_last_reviewed(self):
        expected_last_reviewed = self.user_review.last_reviewed.date()
        received_last_reviewed = self.database_user_review.last_reviewed
        self.assertEqual(expected_last_reviewed, received_last_reviewed)

    def test_computed_interval(self):
        expected_computed_interval = self.user_review.computed_interval
        received_computed_interval = (self.database_user_review.
                                      computed_interval)
        self.assertEqual(expected_computed_interval,
                         received_computed_interval)

    # def test_current_real_interval(self):
    #     # since this is a calculated property and its first argument is
    #     # current date, only 'last_reviewed' must be tested
    #     pass

    def test_easiness_factor(self):
        expected_ef = self.user_review.easiness_factor
        received_ef = self.database_user_review.easiness_factor
        self.assertEqual(expected_ef, received_ef)


class CramTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.card_review_details = {
            "id": "1236435838",
            "tmtrpt": "6574",
            "stmtrpt": "6574",
            "livl": "1274",
            "rllivl": "1764",
            "ivl": "583",
            "rp": "6",
            "gr": "4"
        }
        User = get_user_model()
        cls.user = User(username="user")
        cls.user.save()
        cls.time_of_start = 1186655166
        cls.card_data = {
            "question": "question",
            "answer": "answer",
            "review_details": cls.card_review_details
        }

    def test_crammed_false(self):
        """
        Card with grade > 3 shouldn't be crammed.
        """
        card = HtmlFormattedMemorizedCard(self.card_data, self.time_of_start)
        ImportedMemorizedCard(card, self.user)
        database_card = Card.objects.first()
        database_user_review = CardUserData.objects.get(user=self.user,
                                                        card=database_card)
        self.assertFalse(database_user_review.crammed)

    def test_crammed_true(self):
        """
        Card with grade < 4 should be crammed.
        """
        card_review_details = {**self.card_review_details, "gr": "1"}
        card_data = {**self.card_data, "review_details": card_review_details}
        card = HtmlFormattedMemorizedCard(card_data, self.time_of_start)
        ImportedMemorizedCard(card, self.user)
        database_card = Card.objects.first()
        database_user_review = CardUserData.objects.get(user=self.user,
                                                        card=database_card)
        self.assertTrue(database_user_review.crammed)
