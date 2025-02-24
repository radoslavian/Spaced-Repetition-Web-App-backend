import unittest
from datetime import datetime, timedelta

from cards.management.fr_importer.items_parser.modules.user_review import UserReview


class UserReviewTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # from the <fullrecall> opening attribute
        # first day of your FullRecall learning (in Unix time format)
        cls.time_of_start = 1186655166
        # input:
        # ints in xml are represented as strings
        cls.extracted_attributes = {
            # <item>'s attributes:
            # id number (in fact: time of creating item in Unix time format)
            "id": "1236435838",
            # time to repeat
            "tmtrpt": "6574",
            # time to repeat computed on not-ahead-of-scheduled-time review
            "stmtrpt": "6574",
            # last interval computed by ANN (in days; 0-2048)
            "livl": "1274",
            # real last interval (in days; 0-2048)
            "rllivl": "1764",
            # interval (in days; 0-2048)
            "ivl": "499",
            # number of not-ahead-of-scheduled-time reviews (0-128)
            "rp": "6",
            # grade (0-5; 0=the worst, 5=the best)
            "gr": "4"
        }
        time_of_start = datetime.fromtimestamp(cls.time_of_start)
        # output:
        cls.user_review = {
            "computed_interval": timedelta(days=499),
            "lapses": 0,
            "reviews": 6,
            "total_reviews": 6,
            "last_reviewed": time_of_start + timedelta(
                days=int(cls.extracted_attributes["stmtrpt"])) - timedelta(
                days=int(cls.extracted_attributes["ivl"])),
            "introduced_on": datetime.fromtimestamp(
                int(cls.extracted_attributes["id"])),
            # actually the 'next review date'
            "review_date": time_of_start + timedelta(
                days=int(cls.extracted_attributes["stmtrpt"])),
            "grade": int(cls.extracted_attributes["gr"]),
            "easiness_factor": 1.5,
            "crammed": False,
            "comment": None
        }

    def test_conversion(self):
        review = UserReview(self.extracted_attributes, self.time_of_start)
        self.assertDictEqual({**review}, self.user_review)

    def test_ef_too_low(self):
        """
        Should return 1.5 for a card where computed ef is lower than 1.5.
        """
        # the formula is: ivl/rlivl
        rllivl = 271  # last real interval
        ivl = 33  # (current) interval
        expected_ef = 1.5
        review_details = {
            **self.extracted_attributes,
            "rllivl": rllivl,
            "ivl": ivl
        }
        review = UserReview(review_details, self.time_of_start)
        self.assertEqual(expected_ef, review["easiness_factor"])

    def test_ef_right(self):
        """
        Should return not normalized ef (increase to 1.4 or reduce to 3.0).
        """
        rllivl = 673  # last real interval
        ivl = 1397  # (current) interval
        expected_ef = 2.08  # round to two decimal places
        review_details = {
            **self.extracted_attributes,
            "rllivl": rllivl,
            "ivl": ivl
        }
        review = UserReview(review_details, self.time_of_start)
        self.assertEqual(expected_ef, review["easiness_factor"])

    def test_ef_too_high(self):
        """
        Should return 4.0 for a card where a computed ef is higher than 4.0.
        """
        rllivl = 67  # last real interval
        ivl = 1397  # (current) interval
        expected_ef = 4.0
        review_details = {
            **self.extracted_attributes,
            "rllivl": rllivl,
            "ivl": ivl
        }
        review = UserReview(review_details, self.time_of_start)
        self.assertEqual(expected_ef, review["easiness_factor"])

    def test_ef_special_case(self):
        """
        Should return higher ef for cards with successful review and grade > 3.
        Fr has limit of 2048 days that could be assigned to a card
        as an interval. For this
        reason, some cards, even with many successful reviews, will get shorter
        new interval than the previously calculated. In order to prevent this
        such cards should get an arbitrary Ef.
        (Arbitrary) conditions to be met:
        * last real interval > 1000 days
        * current computed interval is shorter than the previous one
        * current computed interval > 500
        * grade is > 3 (that is, 4 or 5)
        * number of reviews > 3
        """
        expected_ef = 2.3
        review_details = {
            **self.extracted_attributes,
            "rllivl": 2048,
            "ivl": 1694,
            "rp": 5,
            "gr": 5
        }
        review = UserReview(review_details, self.time_of_start)
        self.assertEqual(expected_ef, review.easiness_factor)

    def test_interval_ef_div_by_zero(self):
        """
        It is possible  for the interval used for calculating EF to equal 0.
        In this case, the interval used in a division should be set to non-zero
        value.
        """
        review_details = {
            **self.extracted_attributes,
            "rllivl": 0
        }
        review = UserReview(review_details, self.time_of_start)
        self.assertGreater(review.easiness_factor, 0)
