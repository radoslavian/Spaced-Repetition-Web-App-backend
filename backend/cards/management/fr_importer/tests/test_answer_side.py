from unittest import TestCase

from cards.management.fr_importer.modules.phonetics_converter import \
    PhoneticsConverter
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


class FormattedPhonetics(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.answer = "casting vote"
        cls.snd_file = "<snd>snds/english_examples_2714.mp3</snd>"
        cls.img_file = "<img>../obrazy/marihuana.jpg</img>"
        cls.example_sentence = ("The risk of infections affecting your upper"
                                " respiratory tract and lung increases.")
        cls.phonetics = "a2(r)B:_^ju2rgr"

        cls.input_question = (f"{cls.answer}\n"
                              f"vote [{cls.phonetics}]\n"
                              + cls.example_sentence
                              + cls.img_file
                              + cls.snd_file)
        cls.input_question_no_phonetics = "{}\n{}{}{}".format(
            cls.answer, cls.example_sentence,
            cls.img_file, cls.snd_file)

        cls.formatted_phonetics = (
            '<span class="phonetics-entity" title="aʊə - our - as in sour">aʊə'
            '</span><span class="phonetics-entity" title="əː - er - as in '
            'nurse">əː</span><span class="phonetics-entity" title="">_</span>'
            '<span class="phonetics-entity" title="æ - a - as in pat, attack">'
            'æ</span><span class="phonetics-entity" title="jʊər - yoor - as in'
            ' curious">jʊər</span><span class="phonetics-entity" title="ɡr - '
            'as in green">ɡr</span>')

    def test_output(self):
        answer = Answer(self.input_question)
        self.assertEqual(answer.formatted_phonetics, self.formatted_phonetics)

    def test_no_phonetics(self):
        """
        Should return None if there's no phonetics on the card.
        """
        answer = Answer(self.input_question_no_phonetics)
        self.assertIsNone(answer.formatted_phonetics)


class ExampleSentences(CommonCardSideTests, TestCase):
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
        example_sentence = "this     is    example   sentence"
        expected_output = "this is example sentence"
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


class OutputText(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.answer = "simple answer"
        cls.key = "phonetics-key"
        cls.phonetics = "a2(r)B:_^ju2rgr"
        cls.formatted_phonetics = (
            '<span class="phonetic-spelling">'
            '[{}]'.format(PhoneticsConverter(
                cls.phonetics).converted_phonetics)
        + '</span>')
        cls.example_sentences = "sentence 1\nsentence 2"
        cls.answer_component = f'<div class="answer">{cls.answer}</div>'
        cls.phonetics_component = (
            '<div class="phonetics">'
            f'<span class="phonetic-key">{cls.key}</span> '
            f'{cls.formatted_phonetics}</div>')

        cls.answer_key_phonetics = (
            f"{cls.answer}\n{cls.key} [{cls.phonetics}]")
        cls.answer_phonetics_key_examples = (
            f"{cls.answer}\n{cls.key}\n{cls.example_sentences}")
        cls.answer_phonetics_examples = (
            f"{cls.answer} [{cls.phonetics}]\n"
            f"{cls.example_sentences}")

    def test_answer_phonetics_key_phonetics(self):
        answer = Answer(self.answer_key_phonetics)

        self.assertIn(self.answer_component, answer.output_text)
        self.assertIn(self.phonetics_component, answer.output_text)
        self.assertNotIn('class=”answer-example-sentences”',
                         answer.output_text)

    def test_answer_phonetics_key_examples(self):
        """
        Output composed of: answer, phonetics key and examples sentences.
        """
        answer = Answer(self.answer_phonetics_key_examples)
        phonetics_key = ('<div class="phonetics">'
                         f'<span class="phonetic-key">{self.key}</span></div>')
        sentences = "".join(f"<p><span>{sentence}</span></p>" for sentence in
                       self.example_sentences.splitlines())
        example_sentences = (
            f'<div class=”answer-example-sentences”>{sentences}</div>')
        expected_output = (self.answer_component + phonetics_key
                           + example_sentences)
        self.assertEqual(answer.output_text, expected_output)

    def test_answer_phonetics_examples(self):
        answer = Answer(self.answer_phonetics_examples)
        answer_phonetics = (
            f'<div class="answer">{self.answer} '
            f'{self.formatted_phonetics}</div>')
        example_sentences = ('<div class=”answer-example-sentences”><p>'
                             '<span>sentence 1</span></p><p><span>sentence 2'
                             '</span></p></div>')
        expected_output = f"{answer_phonetics}{example_sentences}"
        self.assertEqual(expected_output, answer.output_text)

