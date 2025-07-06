from django.test import TestCase
from cards.utils.exceptions import CardReviewDataExists

class ExceptionCase(TestCase):
    def test_CardReviewDataExists_message(self):
        expected_message = ("Review data for a given user/data pair "
                            + "already exists.")
        self.assertEqual(CardReviewDataExists().message, expected_message)