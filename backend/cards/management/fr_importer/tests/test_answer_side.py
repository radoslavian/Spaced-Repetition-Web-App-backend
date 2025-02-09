from unittest import TestCase

from cards.management.fr_importer.tests.common_card_side_tests import \
    CommonCardSideTests
from cards.management.fr_importer.modules.card_answer import Answer


class GetAnswer(CommonCardSideTests, TestCase):
    """
    Main answer component is located in the first line of an answer side.
    """

    @classmethod
    def setUpClass(cls):
        cls.single_line_answer_no_media = ("<u>some</u> <b><i>answer</i></b> "
                                           "<strike>text</strike>")
        cls.sound_path = ("<snd>snds/he was about to kick the"
                          " ball when he.mp3</snd>")
        cls.image_path = "<img>../obrazy/pike01.jpg</img>"
        cls.phonetics = "[a2'(r)B:_^ju2rgr]"

        cls.single_line_answer_sound = (cls.single_line_answer_no_media
                                        + cls.sound_path)
        cls.single_line_answer_image = (cls.single_line_answer_no_media
                                        + cls.image_path)
        cls.single_line_answer_all_media = (cls.single_line_answer_no_media
                                            + cls.sound_path + cls.image_path)
        cls.single_line_phonetics = f"answer {cls.phonetics}"

        cls.answer_single_line_no_media = Answer(
            cls.single_line_answer_no_media)

    def test_answer_extraction(self):
        expected_output = "some <i>answer</i> <strike>text</strike>"
        self.assertEqual(self.answer_single_line_no_media.answer,
                         expected_output)

    def test_no_illegal_tags(self):
        """
        The (main) answer shouldn't contain bold <b></b> and underline <u></u>
        tags.
        """
        self.assert_no_illegal_formatting_tags(
            self.answer_single_line_no_media.answer)

    def test_no_phonetics(self):
        answer = Answer(self.single_line_phonetics)
        self.assertEqual("answer", answer.answer)

    def test_allowed_tags(self):
        self.assert_allowed_tags(self.answer_single_line_no_media.answer)


class PhoneticsKey(CommonCardSideTests, TestCase):
    @classmethod
    def setUpClass(cls):
        # dash (-) is pretty important in regex matching
        cls.phonetics_key = "key-word"
        cls.phonetics = "[a2'(r)B:_^ju2rgr]"
        cls.answer_only = "answer"
        cls.example_sentence = ("A single word in the second"
                                " line is a phonetics key,"
                                " this is the example sentence."
                                "<img>image/path.jpg</img>"
                                "<snd>sound/path.mp3</snd>")
        cls.answer_example_no_phk = f"answer\n{cls.example_sentence}"
        cls.answer_key_no_phonetics = (f"an answer\n{cls.phonetics_key}\n"
                                       f"{cls.example_sentence}")
        cls.answer_key_phonetics = (
            f"{cls.answer_only}\n<b><u>{cls.phonetics_key}</u></b> "
            f"{cls.phonetics}\n{cls.example_sentence}")

    def test_answer_only(self):
        """
        Should return 'None' if there's an answer only (with no phonetics key).
        """
        answer = Answer(self.answer_only)
        self.assertIsNone(answer.phonetics_key)

    def test_answer_example_sentence(self):
        """
        Should return 'None' if there's  an answer with an example
        sentence (and no phonetics key).
        """
        answer = Answer(self.answer_example_no_phk)
        self.assertIsNone(answer.phonetics_key)

    def test_key_no_phonetics(self):
        """
        Should return the key even if there's no phonetics next to it.
        """
        answer = Answer(self.answer_key_no_phonetics)
        self.assertEqual(self.phonetics_key, answer.phonetics_key)

    def test_key_phonetics(self):
        """
        Should return the key when there is: an answer, key together with
        phonetics, example sentence.
        """
        answer = Answer(self.answer_key_phonetics)
        self.assertEqual(self.phonetics_key, answer.phonetics_key)

    def test_no_illegal_tags(self):
        """
        No <b></b> and <u></u> tags in phonetics key.
        """
        answer = Answer(self.answer_key_phonetics)
        self.assert_no_illegal_formatting_tags(answer.phonetics_key)


class RawPhonetics(CommonCardSideTests, TestCase):
    """
    Tests for extracting raw phonetics (without formatting).
    """

    @classmethod
    def setUpClass(cls):
        cls.answer_single_word = "answer"
        cls.answer_multiple_words = "this is an answer"
        cls.phonetics_key = "phonetics"
        cls.phonetics = "a2'(r)B:_^ju2rgr"
        cls.example_sentences = ("example sentence 1\n"
                                 "example sentence 2")

        cls.phonetics_alongside_answer = (f"{cls.answer_single_word} "
                                          f"<b><u>[{cls.phonetics}]</u></b>")
        cls.phonetics_alongside_key = (
            f"{cls.answer_multiple_words}\n"
            f"{cls.phonetics_key} <u><b>[{cls.phonetics}]</b></u>\n"
            f"{cls.example_sentences}")
        cls.no_phonetics_alongside_answer = (
            f"{cls.answer_single_word}\n"
            f"{cls.example_sentences}")
        cls.no_phonetics_alongside_key = (
            f"{cls.answer_single_word}\n"
            f"{cls.phonetics_key}\n"
            f"{cls.example_sentences}")

    def test_phonetics_alongside_answer(self):
        """
        Extracting phonetics put alongside an answer.
        """
        answer = Answer(self.phonetics_alongside_answer)
        self.assertEqual(self.phonetics, answer.raw_phonetics)

    def test_phonetics_alongside_key(self):
        """
        Extracting phonetics put alongside a phonetics key(word).
        """
        answer = Answer(self.phonetics_alongside_key)
        self.assertEqual(self.phonetics, answer.raw_phonetics)

    def test_no_phonetics_alongside_answer(self):
        """
        Should return 'None' if there's no phonetics alongside an answer.
        """
        answer = Answer(self.no_phonetics_alongside_answer)
        self.assertIsNone(answer.raw_phonetics)

    def test_no_phonetics_alongside_key(self):
        """
        Should return 'None' if there's no phonetics alongside a phonetics key.
        """
        answer = Answer(self.no_phonetics_alongside_key)
        self.assertIsNone(answer.raw_phonetics)

    def test_no_illegal_tags(self):
        """
        Extracted phonetics shouldn't contain illegal tags:
        <b></b><u></u>.
        """
        answer = Answer(self.phonetics_alongside_key)
        self.assert_no_illegal_formatting_tags(answer.raw_phonetics)
