import json
import pprint
import unittest
from datetime import datetime, timedelta

from cards.management.fr_importer.modules.user_review import UserReview


class UserReviewTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # input:
        cls.extracted_attributes = {
            # from the <fullrecall> opening attribute
            # first day of your FullRecall learning (in Unix time format)
            "time_of_start": 1186655166,
            # <item>'s attributes:
            # id number (in fact: time of creating item in Unix time format)
            "id": 1236435838,
            # time to repeat
            "tmtrpt": 6574,
            # time to repeat computed on not-ahead-of-scheduled-time review
            "stmtrpt": 6574,
            # last interval computed by ANN (in days; 0-2048)
            "livl": 1274,
            # real last interval (in days; 0-2048)
            "rllivl": 1764,
            # interval (in days; 0-2048)
            "ivl": 583,
            # number of not-ahead-of-scheduled-time reviews (0-128)
            "rp": 6,
            # grade (0-5; 0=the worst, 5=the best)
            "gr": 4
        }
        time_of_start = datetime.fromtimestamp(
            cls.extracted_attributes["time_of_start"])
        # output:
        cls.user_review = {
            "computed_interval": 583,
            "lapses": 0,
            "reviews": 6,
            "total_reviews": 6,
            "last_reviewed": time_of_start + timedelta(
                days=cls.extracted_attributes["stmtrpt"]) - timedelta(
                days=cls.extracted_attributes["ivl"]),
            "introduced_on": datetime.fromtimestamp(
                cls.extracted_attributes["id"]),
            # actually the 'next review date'
            "review_date": time_of_start + timedelta(
                days=cls.extracted_attributes["stmtrpt"]),
            "grade": cls.extracted_attributes["gr"],
            "easiness_factor": 2.0,
            "crammed": False,
            "comment": None
        }

    def test_conversion(self):
        review = UserReview(self.extracted_attributes)
        self.assertDictEqual({**review}, self.user_review)

    def test_ef_minimal(self):
        """
        EF 1.8 for interval computed at < 300.
        """
        easiness = 1.8
        user_review = {**self.extracted_attributes, "ivl": 299}
        review = UserReview(user_review)
        self.assertEqual(easiness, review.easiness_factor)

    def test_ef_average(self):
        """
        EF 2.0 for interval equal or longer than 300 and shorter than 600 days.
        """
        easiness = 2.0
        user_review_lower_bound = {**self.extracted_attributes, "ivl": 300}
        user_review_upper_bound = {**self.extracted_attributes, "ivl": 599}
        review_lower_bound = UserReview(user_review_lower_bound)
        review_upper_bound = UserReview(user_review_upper_bound)

        self.assertEqual(easiness, review_lower_bound.easiness_factor)
        self.assertEqual(easiness, review_upper_bound.easiness_factor)

    def test_ef_medium(self):
        """
        EF 2.5 for interval computed at 600-999 days.
        """
        easiness = 2.5
        user_review_lower_bound = {**self.extracted_attributes, "ivl": 600}
        user_review_upper_bound = {**self.extracted_attributes, "ivl": 999}
        review_lower_bound = UserReview(user_review_lower_bound)
        review_upper_bound = UserReview(user_review_upper_bound)

        self.assertEqual(easiness, review_lower_bound.easiness_factor)
        self.assertEqual(easiness, review_upper_bound.easiness_factor)

    def test_ef_max(self):
        """
        EF 3.0 for interval computed at 1000+
        """
        easiness = 3.0
        user_review = {**self.extracted_attributes, "ivl": 1000}
        review = UserReview(user_review)

        self.assertEqual(easiness, review.easiness_factor)

    def test_invalid_interval(self):
        """
        Raises ValueError in case of interval lower than 0.
        """
        user_review = {**self.extracted_attributes, "ivl": -10}
        self.assertRaises(ValueError,
                          lambda: UserReview(user_review).easiness_factor)
