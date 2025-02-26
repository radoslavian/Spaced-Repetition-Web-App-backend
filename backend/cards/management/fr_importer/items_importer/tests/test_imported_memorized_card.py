from datetime import datetime

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
        pass

    def test_computed_interval(self):
        pass

    def test_last_real_interval(self):
        # can't be set, test only
        pass

    def test_easiness_factor(self):
        pass

    def test_crammed_false(self):
        """
        Shouldn't be added to the cram queue.
        """
        pass

    def test_crammed_true(self):
        """
        Should be added to the cram queue.
        """
        pass
