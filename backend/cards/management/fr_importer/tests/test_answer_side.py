import unittest

from cards.management.fr_importer.modules.phonetics_converter import \
    PhoneticsConverter
from cards.management.fr_importer.tests.common_card_side_tests import \
    CommonCardSideTests
from cards.management.fr_importer.modules.card_answer import Answer


class GetAnswer(CommonCardSideTests, unittest.TestCase):
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
        """
        Only answer text should be extracted into .answer field.
        """
        answer = Answer(self.single_line_phonetics)
        self.assertEqual("answer", answer.answer)

    def test_allowed_tags(self):
        self.assert_allowed_tags(self.answer_single_line_no_media.answer)


class PhoneticsKey(CommonCardSideTests, unittest.TestCase):
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


class RawPhonetics(CommonCardSideTests, unittest.TestCase):
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
        self.assertEqual(self.phonetics, answer.raw_phonetics_spelling)

    def test_phonetics_alongside_key(self):
        """
        Extracting phonetics put alongside a phonetics key(word).
        """
        answer = Answer(self.phonetics_alongside_key)
        self.assertEqual(self.phonetics, answer.raw_phonetics_spelling)

    def test_no_phonetics_alongside_answer(self):
        """
        Should return 'None' if there's no phonetics alongside an answer.
        """
        answer = Answer(self.no_phonetics_alongside_answer)
        self.assertIsNone(answer.raw_phonetics_spelling)

    def test_no_phonetics_alongside_key(self):
        """
        Should return 'None' if there's no phonetics alongside a phonetics key.
        """
        answer = Answer(self.no_phonetics_alongside_key)
        self.assertIsNone(answer.raw_phonetics_spelling)

    def test_no_illegal_tags(self):
        """
        Extracted phonetics shouldn't contain illegal tags:
        <b></b><u></u>.
        """
        answer = Answer(self.phonetics_alongside_key)
        self.assert_no_illegal_formatting_tags(answer.raw_phonetics_spelling)


class ExampleSentences(CommonCardSideTests, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.answer = "answer"
        cls.key = "phonetics-key"
        cls.phonetics = "a2(r)B:_^ju2rgr"
        cls.example_sentences = ["example <b><u><i>sentence</i></u></b> 1",
                                 "<strike>example</strike> sentence 2"]
        cls.cleaned_example_sentences = ["example <i>sentence</i> 1",
                                         "<strike>example</strike> sentence 2"]
        cls.example_sentences_text = "\n".join(cls.example_sentences)
        cls.snd_file = "<snd>snds/english_examples_2714.mp3</snd>"
        cls.img_file = "<img>../obrazy/marihuana.jpg</img>"

        cls.answer_phonetics_key_phonetics = (
            "{answer}\n{key} [{phonetics}]{snd_file}{img_file}"
            .format(answer=cls.answer, key=cls.key, phonetics=cls.phonetics,
                    snd_file=cls.snd_file, img_file=cls.img_file))
        cls.answer_sentences = (f"{cls.answer}\n"
                                f"{cls.example_sentences_text}"
                                f"{cls.img_file}{cls.snd_file}")
        cls.answer_phonetics_sentences = (f"{cls.answer} [{cls.phonetics}]\n"
                                          f"{cls.example_sentences_text}"
                                          f"{cls.img_file}{cls.snd_file}")
        cls.answer_phonetics_key_phonetics_sentences = (
            f"{cls.answer}\n{cls.key} [{cls.phonetics}]"
            f"\n{cls.example_sentences_text}")

    def test_answer_no_example_sentences(self):
        """
        Should return an empty list.
        """
        answer = Answer(self.answer)
        self.assertIs(list, type(answer.example_sentences))
        self.assertFalse(answer.example_sentences)

    def test_answer_phonetics_key_phonetics(self):
        """
        Should return an empty list.
        """
        answer = Answer(self.answer_phonetics_key_phonetics)
        self.assertIs(list, type(answer.example_sentences))
        self.assertFalse(answer.example_sentences)

    def test_answer_sentences(self):
        """
        Should return list of sentences.
        """
        answer = Answer(self.answer_sentences)
        self.assertListEqual(answer.example_sentences,
                             self.cleaned_example_sentences)

    def test_answer_phonetics_sentences(self):
        """
        Should return list of sentences.
        """
        answer = Answer(self.answer_phonetics_sentences)
        self.assertListEqual(answer.example_sentences,
                             self.cleaned_example_sentences)

    def test_answer_phonetics_key_phonetics_sentences(self):
        """
        Should return list of sentences.
        """
        answer = Answer(self.answer_phonetics_key_phonetics_sentences)
        self.assertListEqual(answer.example_sentences,
                             self.cleaned_example_sentences)

    def test_multiple_spaces_in_example(self):
        """
        Should merge multiple spaces into one.
        """
        example_sentence = "this     is    an example   sentence"
        expected_output = "this is an example sentence"
        answer_text = f"{self.answer}\n{example_sentence}"
        answer = Answer(answer_text)
        self.assertEqual(expected_output, answer.example_sentences[0])

    def _print_cases(self):
        """
        For inspecting test cases.
        Add 'test' at the start of the function name to run it.
        """
        print("\nAnswer, phonetics key, phonetics:\n"
              "{}".format(self.answer_phonetics_key_phonetics))
        print("\nAnswer, sentence:\n{}".format(self.answer_sentences))
        print("\nAnswer, phonetics, sentences:\n{}".format(
            self.answer_phonetics_sentences))
        print("\nAnswer, phonetics key, phonetics, sentences:\n{}"
              .format(self.answer_phonetics_key_phonetics_sentences))


class ExtraText(unittest.TestCase):
    """
    Extracting extra text after answer + phonetics/phonetics key + phonetics.
    """
    @classmethod
    def setUpClass(cls):
        cls.words_after_answer = ("assent [2's2nt] (zgoda; aprobata)"
                                  "<snd>snds/english_examples_2098.mp3</snd>")
        cls.words_after_phonetics_key = (
            "seethed\n"
            "<b>seethe [si:9] (~burzyć się)</b>)\n"
            "The elements of that war had been seething in English society."
            "<snd>snds/his_brain_had_no.mp3</snd>")

    def test_extra_text_after_phonetics_key(self):
        answer = Answer(self.words_after_phonetics_key)
        extra_words = "(~burzyć się)"
        phonetics_key = "seethe"

        self.assertIn(extra_words, answer.phonetics_key)
        self.assertIn(phonetics_key, answer.phonetics_key)

    def test_extra_text_after_answer(self):
        answer = Answer(self.words_after_answer)
        extra_words = "(zgoda; aprobata)"
        answer_text = "assent"

        self.assertIn(extra_words, answer.answer)
        self.assertIn(answer_text, answer.answer)
