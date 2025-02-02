import re

from unittest import TestCase

from cards.management.fr_importer.modules.question_side import Question


class QuestionSplitMediaTags(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.definition = "Some definition text"
        cls.example = "Example line 1"
        cls.question_only = (
            f"{cls.definition}"
            "<img>../obrazy/swimmer-mike-paget.jpg</img><snd>snds/not "
            "aware of or careful.mp3</snd>")
        cls.cleaned_question = cls.definition
        cls.question_example_snd = (
            f"<b>{cls.definition}</b>\n"
            f"{cls.example}"
            "<snd>snds/english_examples_2806.mp3</snd>")
        cls.question_example_img = (
            f"<b>{cls.definition}</b>\n"
            f"{cls.example}"
            "<img>../obrazy/wedding_077.jpg</img>")
        cls.question_example_all_media = (
            f"<b>{cls.definition}</b>\n"
            f"{cls.example}"
            "<img>../obrazy/wedding_077.jpg</img><snd>snds/english_"
            "examples_2806.mp3</snd>")

    def test_stripping_media_from_definition(self):
        """
        Removes media tags from cards with definition only (no example).
        """
        item_question = Question(self.question_only)
        self.assertEqual(item_question.definition,
                         self.cleaned_question)
        self.assertFalse(item_question.example)

    def test_stripping_snd(self):
        """
        Removes snd tag (with contents) from the card (definition and example).
        """
        question = Question(self.question_example_snd)
        self.assertEqual(question.definition, self.cleaned_question)
        self.assertEqual(question.example, self.example)

    def test_stripping_img(self):
        """
        No img tag (with contents) in the card (definition and example).
        """
        question = Question(self.question_example_img)
        self.assertEqual(question.definition, self.cleaned_question)
        self.assertEqual(question.example, self.example)

    def test_stripping_all_media_definition_example(self):
        """
        No media tags (and their contents) in the card (definition
        and example).
        """
        question = Question(self.question_example_all_media)
        self.assertEqual(question.definition, self.cleaned_question)
        self.assertEqual(question.example, self.example)


class QuestionDefinitionExampleTestCase(TestCase):
    """
    Tests definition and example from the Question
    + takes the definition from:
     - a card with a definition only
     - a card with a definition and an example sentence
    + removes the bold and italic tags (present in test data).
    """

    @classmethod
    def setUpClass(cls):
        cls.basic_question = "basic question"
        cls.definition = "Definition for word in example"
        cls.example = "Example line 1 [...]\nLine 2"
        cls.example_transformed = "<i>Example line 1 [...]<br/>Line 2</i>"
        cls.question_example = (
            f"<b>{cls.definition}</b>\n"
            f"<i>{cls.example}</i>")

    def test_definition_only(self):
        """
        Card with definition and no example.
        """
        item_question = Question(self.basic_question)
        self.assertEqual(item_question.definition, self.basic_question)
        self.assertFalse(item_question.example)

    def test_definition(self):
        """
        Extracts definition from a card with a definition and example.
        """
        item_question = Question(self.question_example)
        self.assertEqual(item_question.definition, self.definition)

    def test_example(self):
        """
        Extracts example from a card with a definition and example.
        """
        item_question = Question(self.question_example)
        self.assertEqual(item_question.example, self.example_transformed)


class RedundantWhiteCharactersQuestion(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.multiple_spaces = "some   text"
        cls.multiple_newlines = "some\n\n\n\n\n\ntext"

    def test_merging_newlines_example(self):
        card_side = f"some definition\n{self.multiple_newlines}"
        question = Question(card_side)
        expected_number_of_newlines = 1
        newline = "<br/>"
        self.assertEqual(expected_number_of_newlines,
                         question.example.count(newline))

    def test_merging_spaces_definition(self):
        question = Question(self.multiple_spaces)
        space = " "
        expected_number_of_spaces = 1
        self.assertEqual(expected_number_of_spaces,
                         question.definition.count(space))

    def test_merging_spaces_example(self):
        card_side = f"some word definition\n{self.multiple_spaces}"
        question = Question(card_side)
        space = " "
        expected_number_of_spaces = 1
        self.assertEqual(expected_number_of_spaces,
                         question.example.count(space))


class QuestionAllowedTags(TestCase):
    """
    All formatting tags in the Question side should be removed except <strike>.
    """

    @classmethod
    def setUpClass(cls):
        question = ("definition: <i><b><strike>definition</strike></b></i>\n"
                    "example: <b><strike><i>example</i></strike></b>")
        cls.card_question = Question(question)

    def test_allowed_tags_in_definition(self):
        """
        Should keep <strike> and <i> tags in definition.
        """
        expected_output = "definition: <i><strike>definition</strike></i>"
        self.assertEqual(self.card_question.definition, expected_output)

    def test_allowed_tags_in_example(self):
        """
        Should keep <strike> and <i> tags in example.
        """
        expected_output = "example: <strike><i>example</i></strike>"
        self.assertEqual(self.card_question.example, expected_output)


class QuestionOutputText(TestCase):
    """
    Tests Question's output - Question._get_output_text() and it's accessor -
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
        cls.question = Question(cls.question_unparsed)

    def test_card_definition(self):
        """
        Output should contain div class=”card-question-definition” field
        with definition.
        """
        formatted_definition = ('<div class="card-question-definition"><p>'
                                f'<i>{self.definition}</i>'
                                '</p></div>')
        self.assertIn(formatted_definition, self.question.output_text)

    def test_separating_hr(self):
        """
        There should be a hr line between question and answer.
        """
        pattern = re.compile(".*card-question-definition.*"
                             f"{self.hr_for_re}.*"
                             "</p></div>")
        self.assertTrue(re.match(pattern, self.question.output_text))

    def test_card_example(self):
        """
        Output should contain div class=”card-question-example” field
        with example.
        """
        formatted_example = ('<div class="card-question-example"><p>'
                             f'{self.example}'
                             f'</p></div>')
        self.assertIn(formatted_example, self.question.output_text)

    def test_no_example(self):
        """
        There should be no:
        * Formatting tags for question's example sentence
        if the field for it is empty.
        * hr if there is no example.
        """
        question = Question(self.definition)
        formatted_example_tags = '<div class="card-question-example">'
        hr = '<hr class="question-example-separating-hr"/>'

        self.assertNotIn(hr, question.output_text)
        self.assertNotIn(formatted_example_tags, question.output_text)


class QuestionTextPlaceholders(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.definition = ("definition of some [...] and "
                          "[unusual and tasty] word")
        cls.placeholder = ('<span class="extracted-text" title="guess the '
                           'missing part">[&hellip;]</span>')
        cls.question = Question(cls.definition)

    def test_text_placeholder(self):
        """
        [...] in an example should be changed into:
        <span class="extracted-text" title="guess the missing part>
        [&hellip;]</span>
        """
        text_with_placeholder = f"definition of some {self.placeholder} and"
        self.assertIn(text_with_placeholder, self.question.output_text)

    def test_highlighted_text(self):
        """
        some text [other text] another text - text within [...] should
        be put into span:
        <span class="highlighted-text">[other text]</span>
        """
        text_with_highlighted_words = ('and <span class="highlighted-text">'
                                      '[unusual and tasty]</span> word')
        self.assertIn(text_with_highlighted_words, self.question.output_text)
