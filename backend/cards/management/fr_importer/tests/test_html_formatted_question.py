import re
from unittest import TestCase

from cards.management.fr_importer.modules.html_formatted_question import HTMLFormattedQuestion


class QACardQuestionFormattedFields(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.card_definition = "card definition"
        cls.examples = "example 1\nexample 2"
        cls.question = f"{cls.card_definition}\n{cls.examples}"
        cls.card = HTMLFormattedQuestion(cls.question)

    def test_definition(self):
        """
        Card definition should be enclosed into formatting html.
        """
        expected_output = ('<div class="card-question-definition">'
                           f'<p>{self.card_definition}</p>'
                           '</div>')
        self.assertEqual(expected_output, self.card.definition)

    def test_formatted_examples(self):
        expected_output = ["<p>example 1</p>", "<p>example 2</p>"]
        self.assertEqual(expected_output,
                         self.card.examples)

    def test_example_sentences(self):
        expected_output = ('<div class="card-question-example">'
                           '<p>example 1</p><p>example 2</p>'
                           '</div>')
        self.assertEqual(expected_output, self.card.examples_block)

    def test_no_examples(self):
        """
        Shouldn't make examples block if there are no example sentences.
        """
        card = HTMLFormattedQuestion(self.card_definition)
        self.assertFalse(card.examples_block)


class QuestionTextHighlighting(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.definition = ("definition of some [...] and "
                          "[unusual and - tasty] word")
        cls.example_sentence = "example [highlighted text] of [...] sentence"
        cls.placeholder = '<span class="highlighted-text">[&hellip;]</span>'
        cls.question = HTMLFormattedQuestion(
            f"{cls.definition}\n{cls.example_sentence}")

    def test_text_placeholder(self):
        """
        [...] in a definition and an example should be highlighted and
        changed into [&hellip;]
        """
        definition_placeholder = f"definition of some {self.placeholder} and"
        example_sentence_placeholder = f"of {self.placeholder} sentence"

        self.assertIn(example_sentence_placeholder, self.question.examples[0])
        self.assertIn(definition_placeholder, self.question.definition)

    def test_highlighted_text(self):
        """
        some text [other text] another text - text within [...] should
        be put into span:
        <span class="highlighted-text">[other text]</span>
        """
        definition_highlighted_words = ('and <span class="highlighted-text">'
                                      '[unusual and - tasty]</span> word')
        example_highlighted_words = (
            'example <span class="highlighted-text">[highlighted '
            'text]</span> of')

        self.assertIn(definition_highlighted_words, self.question.definition)
        self.assertIn(example_highlighted_words, self.question.examples[0])

    def test_highlighted_text_with_dots(self):
        """
        some [text...] and [...text...] should be highlighted.
        """
        question_text = ("first line\nsome [text...] and"
                         " [...text... t...]")
        question = HTMLFormattedQuestion(question_text)
        expected_1 = '<span class="highlighted-text">[text&hellip;]</span>'
        expected_2 = ('<span class="highlighted-text">'
                      '[&hellip;text&hellip; t&hellip;]</span>')

        self.assertIn(expected_1, question.output_text)
        self.assertIn(expected_2, question.output_text)



class QACardQuestionOutputText(TestCase):
    """
    Tests Question's output - Question.output_text() and it's accessor -
    Question.output_text.
    """

    @classmethod
    def setUpClass(cls):
        cls.definition = ("people who are curious about and "
                          "interested in seeing what might be "
                          "happening;")
        cls.definition_malformed_tags = f"<b><i>{cls.definition}</i></b>"
        cls.example = (
            "were kept away by "
            "high-security surveillance systems"
            " and three guard dogs, while the pungent smell of the marijuana "
            "plants was covered up by keeping pigs and chickens on site.")
        cls.question_unparsed = (
            f"{cls.definition_malformed_tags}\n"
            f"{cls.example}"
            "<img>../obrazy/prying-eye-B.jpg</img><snd>snds/"
            "english_examples_0289.mp3</snd>")

        cls.hr_for_re = '<hr class="question-example-separating-hr"\/>'
        cls.card = HTMLFormattedQuestion(question=cls.question_unparsed)


    def test_card_definition(self):
        """
        Output should contain div class=”card-question-definition” field
        with definition.
        """
        formatted_definition = ('<div class="card-question-definition"><p>'
                                f'<i>{self.definition}</i>'
                                '</p></div>')
        self.assertIn(formatted_definition, self.card.output_text)

    def test_separating_hr(self):
        """
        There should be a hr line between question and answer.
        """
        pattern = re.compile(".*card-question-definition.*"
                             f"{self.hr_for_re}.*"
                             "</p></div>")
        self.assertTrue(re.match(pattern, self.card.output_text))

    def test_card_example(self):
        """
        Output should contain div class=”card-question-example” field
        with example.
        """
        formatted_example = ('<div class="card-question-example"><p>'
                             f'{self.example}'
                             f'</p></div>')
        self.assertIn(formatted_example, self.card.output_text)

    def test_no_example(self):
        """
        There should be no:
        * Formatting tags for question's example sentence
        if the field for it is empty.
        * hr if there is no example.
        """
        question = HTMLFormattedQuestion(self.definition)
        formatted_example_tags = '<div class="card-question-example">'
        hr = '<hr class="question-example-separating-hr"/>'

        self.assertNotIn(hr, question.output_text)
        self.assertNotIn(formatted_example_tags, question.output_text)
