import re

from unittest import TestCase

from cards.management.fr_importer.modules.card_question import Question
from cards.management.fr_importer.tests.common_card_side_tests import \
    CommonCardSideTests


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
        self.assertFalse(item_question.examples)

    def test_stripping_snd(self):
        """
        Removes snd tag (with contents) from the card (definition and example).
        """
        question = Question(self.question_example_snd)
        self.assertEqual(question.definition, self.cleaned_question)
        self.assertListEqual(question.examples, [self.example])

    def test_stripping_img(self):
        """
        No img tag (with contents) in the card (definition and example).
        """
        question = Question(self.question_example_img)
        self.assertEqual(question.definition, self.cleaned_question)
        self.assertListEqual(question.examples, [self.example])

    def test_stripping_all_media_definition_example(self):
        """
        No media tags (and their contents) in the card (definition
        and example).
        """
        question = Question(self.question_example_all_media)
        self.assertEqual(question.definition, self.cleaned_question)
        self.assertListEqual(question.examples, [self.example])


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
        cls.example = "Example <i>line 1</i>\nLine 2"
        cls.examples_transformed = ["Example <i>line 1</i>",
                                    "Line 2"]
        cls.question_example = (
            f"<b>{cls.definition}</b>\n"
            f"{cls.example}")

    def test_definition_only(self):
        """
        Card with definition and no example.
        """
        item_question = Question(self.basic_question)
        self.assertEqual(item_question.definition, self.basic_question)
        self.assertFalse(item_question.examples)

    def test_definition_example(self):
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
        self.assertListEqual(item_question.examples, self.examples_transformed)

    def test_raises_if_no_question(self):
        """
        Should raise exception if there's no header (definition).
        """
        self.assertRaises(ValueError, lambda: Question("").definition)


class RedundantWhiteCharactersQuestion(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.multiple_spaces = "some   text"
        cls.multiple_newlines = "some\n\n\n\n\n\ntext"

    def test_merging_newlines_example(self):
        card_side = f"some definition\n{self.multiple_newlines}"
        question = Question(card_side)
        expected_number_of_examples = 2
        self.assertEqual(expected_number_of_examples,
                         len(question.examples))

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
                         question.examples[0].count(space))


class QuestionAllowedIllegalTags(CommonCardSideTests, TestCase):
    """
    All formatting tags in the Question side should be removed except <strike>
    and <i>.
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
        self.assert_allowed_tags(self.card_question.definition)

    def test_illegal_tags_in_definition(self):
        """
        No <b> and <u> tags in definition.
        """
        self.assert_no_illegal_formatting_tags(self.card_question.definition)

    def test_allowed_tags_in_examples(self):
        """
        Should keep <strike> and <i> tags in example.
        """
        self.assert_allowed_tags(self.card_question.examples[0])

    def test_illegal_tags_in_example(self):
        """
        No <b> and <u> tags in example.
        """
        self.assert_no_illegal_formatting_tags(self.card_question.examples)
