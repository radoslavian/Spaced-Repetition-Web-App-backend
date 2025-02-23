from unittest import TestCase

from cards.management.fr_importer.items_parser.modules.html_formatted_answer import \
    HTMLFormattedAnswer
from cards.management.fr_importer.items_parser.modules.phonetics_converter import \
    PhoneticsConverter


class Fields(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.answer_text = "answer"
        cls.phonetics_key = "key"
        cls.phonetics = "dIn6n3i:ItB:ri:"
        cls.formatted_phonetics = PhoneticsConverter(
            cls.phonetics).converted_phonetics
        cls.examples = "sentence 1\nsentence 2"
        cls.side_text_no_key = (f"{cls.answer_text} "
                                f"[{cls.phonetics}]\n{cls.examples}")
        cls.side_text_answer_key_phonetics_examples = (
            f"{cls.answer_text}\n"
            f"{cls.phonetics_key} [{cls.phonetics}]\n"
            f"{cls.examples}")

    def test_no_phonetics_key(self):
        answer = HTMLFormattedAnswer(self.side_text_no_key)
        self.assertIsNone(answer.phonetics_key)

    def test_phonetics_key(self):
        phonetics_key = ('<span class="phonetic-key">'
                         f'{self.phonetics_key}'
                         '</span>')
        answer = HTMLFormattedAnswer(
            self.side_text_answer_key_phonetics_examples)
        self.assertEqual(phonetics_key, answer.phonetics_key)

    def test_phonetics_block(self):
        answer = HTMLFormattedAnswer(
            self.side_text_answer_key_phonetics_examples)
        self.assertIn(self.formatted_phonetics, answer.phonetics_block)
        self.assertIn('<div class="phonetics">',
                      answer.phonetics_block)

    def test_phonetics_spelling_block(self):
        answer = HTMLFormattedAnswer(
            self.side_text_answer_key_phonetics_examples)
        block = ('<span class="phonetic-spelling">'
                 f'[{self.formatted_phonetics}]'
                 '</span>')
        self.assertEqual(block, answer.phonetics_spelling_block)

    def test_answer(self):
        answer = HTMLFormattedAnswer(self.answer_text)
        expected_output = f'<div class="answer">{self.answer_text}</div>'
        self.assertEqual(expected_output, answer.answer)

    def test_example_sentences(self):
        answer = HTMLFormattedAnswer(self.side_text_no_key)
        expected = ["<p><span>sentence 1</span></p>",
                    "<p><span>sentence 2</span></p>"]
        self.assertListEqual(expected, answer.example_sentences)

    def test_example_sentences_block(self):
        joined_examples = "".join(["<p><span>sentence 1</span></p>",
                                   "<p><span>sentence 2</span></p>"])
        expected = ('<div class=”answer-example-sentences”>'
                    + joined_examples
                    + '</div>')
        answer = HTMLFormattedAnswer(self.side_text_no_key)
        self.assertEqual(expected, answer.example_sentences_block)


class Answer(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.answer = "answer"
        cls.phonetics = "I"
        cls.card_text = f"{cls.answer} [{cls.phonetics}]"

    def test_answer_with_phonetics(self):
        """
        Answer with tags, phonetics, tags for phonetics surrounding span.
        """
        answer = HTMLFormattedAnswer(self.card_text)
        phonetics = PhoneticsConverter("I").converted_phonetics

        self.assertIn('<div class="answer">', answer.answer)
        self.assertIn(self.answer, answer.answer)
        self.assertIn(f"[{phonetics}]", answer.answer)
        self.assertIn('<span class="phonetic-spelling">',
                      answer.answer)

    def test_answer_no_phonetics(self):
        """
        Div for answer, answer + closing div.
        """
        answer = HTMLFormattedAnswer(self.answer)
        expected_regex = f"{self.answer}</div>$"

        self.assertIn('<div class="answer">', answer.answer)
        self.assertRegex(answer.answer, expected_regex)


class FormattedPhonetics(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.answer = "casting vote"
        cls.snd_file = "<snd>snds/english_examples_2714.mp3</snd>"
        cls.img_file = "<img>../obrazy/marihuana.jpg</img>"
        cls.example_sentence = ("The risk of infections affecting your upper"
                                " respiratory tract and lung increases.")
        cls.phonetics = "a2(r)B:_^ju2rgr"

        cls.input_answer = (f"{cls.answer}\n"
                            f"vote [{cls.phonetics}]\n"
                            + cls.example_sentence
                            + cls.img_file
                            + cls.snd_file)
        cls.input_answer_no_phonetics = "{}\n{}{}{}".format(
            cls.answer, cls.example_sentence,
            cls.img_file, cls.snd_file)

        cls.formatted_phonetics = (
            '<span class="phonetic-entity" title="aʊə - our - as in sour">aʊə'
            '</span><span class="phonetic-entity" title="əː - er - as in '
            'nurse">əː</span><span class="phonetic-entity" title="">_</span>'
            '<span class="phonetic-entity" title="æ - a - as in pat, attack">'
            'æ</span><span class="phonetic-entity" title="jʊər - yoor - as in'
            ' curious">jʊər</span><span class="phonetic-entity" title="ɡr - '
            'as in green">ɡr</span>')

    def test_output(self):
        answer = HTMLFormattedAnswer(self.input_answer)
        self.assertEqual(answer.phonetics_spelling,
                         self.formatted_phonetics)

    def test_no_phonetics(self):
        """
        Should return None if there's no phonetics on the card.
        """
        answer = HTMLFormattedAnswer(self.input_answer_no_phonetics)
        self.assertIsNone(answer.phonetics_spelling)


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
        answer = HTMLFormattedAnswer(self.answer_key_phonetics)

        self.assertIn(self.answer_component, answer.output_text)
        self.assertIn(self.phonetics_component, answer.output_text)
        self.assertNotIn('class=”answer-example-sentences”',
                         answer.output_text)

    def test_answer_phonetics_key_examples(self):
        """
        Output composed of: answer, phonetics key and examples sentences.
        """
        answer = HTMLFormattedAnswer(self.answer_phonetics_key_examples)
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
        answer = HTMLFormattedAnswer(self.answer_phonetics_examples)
        answer_phonetics = (
            f'<div class="answer">{self.answer} '
            f'{self.formatted_phonetics}</div>')
        example_sentences = ('<div class=”answer-example-sentences”><p>'
                             '<span>sentence 1</span></p><p><span>sentence 2'
                             '</span></p></div>')
        expected_output = f"{answer_phonetics}{example_sentences}"
        self.assertEqual(expected_output, answer.output_text)
