import unittest

from cards.management.fr_importer.modules.html_memorized_card import \
    HtmlFormattedMemorizedCard


class HtmlFormattedMemorizedCardMapping(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # attribute of the <fullrecall ...></fullrecall> tag
        cls.time_of_start = 1186655166

        # attributes of an <item ...></item> tag
        cls.card_review_details = {
            "id": 1236435838,
            "tmtrpt": 6574,
            "stmtrpt": 6574,
            "livl": 1274,
            "rllivl": 1764,
            "ivl": 583,
            "rp": 6,
            "gr": 4
        }
        cls.card_details = {
            "question": "card question",
            "answer": "card answer",
            "review_details": cls.card_review_details
        }
        cls.card = HtmlFormattedMemorizedCard(
            cls.card_details, cls.time_of_start)
        cls.card_mapped = dict(cls.card)

    def test_keys(self):
        self.assertIn("review_details", self.card_mapped)
        self.assertIn("question", self.card_mapped)
        self.assertIn("output_text", self.card_mapped["question"])
        self.assertIn("output_text", self.card_mapped["answer"])
        self.assertIn("answer", self.card_mapped)
        self.assertIn("grade", self.card_mapped["review_details"])

    def test_values(self):
        # presence of a single value from each
        # object (question, answer, user-details):
        self.assertIn(self.card_details["question"],
                      self.card_mapped["question"]["output_text"])
        self.assertIn(self.card_details["answer"],
                      self.card_mapped["answer"]["output_text"])
        self.assertEqual(self.card_review_details["gr"],
                         self.card_mapped["review_details"]["grade"])
