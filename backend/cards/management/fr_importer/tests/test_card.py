import unittest

from cards.management.fr_importer.modules.html_formatted_card import \
    HtmlFormattedCard


class CardInstantiationAndFields(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.definition = "card definition"
        cls.answer = "card answer"
        cls.card = HtmlFormattedCard(cls.definition, cls.answer)

    def test_exception(self):
        """
        Should raise 'ValueError' if whichever __init__ argument is missing
        or empty.
        """
        self.assertRaises(ValueError, lambda: HtmlFormattedCard(
            "question", ""))
        self.assertRaises(ValueError, lambda: HtmlFormattedCard(
            "", "answer"))

    def test_question_output_text(self):
        self.assertIn(self.definition, self.card.question_output_text)

    def test_answer_output_text(self):
        self.assertIn(self.answer, self.card.answer_output_text)


class CardMapping(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.card = HtmlFormattedCard("question", "answer")
        cls.mapped = dict(cls.card)
        cls.expected_keys = {"output_text", "image_file_path",
                             "image_file_name", "sound_file_path",
                             "sound_file_name"}

    def test_question_exists(self):
        self.assertIn("question", self.mapped.keys())

    def test_question_keys(self):
        keys = set(self.mapped["question"].keys())
        self.assertSetEqual(self.expected_keys, keys)

    def test_question_output_text(self):
        self.assertEqual(self.card.question_output_text,
                         self.mapped["question"]["output_text"])

    def test_answer_exists(self):
        self.assertIn("answer", self.mapped.keys())

    def test_answer_keys(self):
        keys = set(self.mapped["answer"].keys())
        self.assertSetEqual(self.expected_keys, keys)

    def test_answer_output_text(self):
        self.assertEqual(self.card.answer_output_text,
                         self.mapped["answer"]["output_text"])
