import unittest

from cards.management.fr_importer.modules.html_formatted_card import \
    HtmlFormattedCard


class CardInstantiationAndFields(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.definition = "card definition"
        cls.answer = "card answer"
        cls.card_data = dict(question=cls.definition, answer=cls.answer)
        cls.card = HtmlFormattedCard(cls.card_data)

    def test_exception(self):
        """
        Should raise 'ValueError' if whichever: question or answer is empty.
        """
        card_no_question = {**self.card_data, "question": ""}
        card_no_answer = {**self.card_data, "answer": ""}
        self.assertRaises(ValueError, lambda: HtmlFormattedCard(
            card_no_answer))
        self.assertRaises(ValueError, lambda: HtmlFormattedCard(
            card_no_question))

    def test_question_output_text(self):
        self.assertIn(self.definition, self.card.question_output_text)

    def test_answer_output_text(self):
        self.assertIn(self.answer, self.card.answer_output_text)


class CardMapping(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        card_data = {"question": "question", "answer": "answer"}
        cls.card = HtmlFormattedCard(card_data)
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
