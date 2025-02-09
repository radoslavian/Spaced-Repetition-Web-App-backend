import re

from cards.management.fr_importer.modules.card_side import CardSide
from cards.management.fr_importer.modules.phonetics_converter import \
    PhoneticsConverter
from cards.utils.helpers import compose


class Answer(CardSide):
    def __init__(self, answer):
        """
        answer - content of <item><a></a></item> tags.
        """
        super().__init__(answer)
        self.phonetics_pattern = r"\[[\w\d'^_\-():]+]"
        self.word_pattern = "[\w.,?-]+"

    def _get_phonetics_key(self) -> str | None:
        words = self._get_split_phonetics_line()
        if not words:
            return
        word = self._match_phonetics_key(words)

        return word

    def _match_phonetics_key(self, words: list) -> str | None:
        word = None
        match len(words):
            case 1:
                if re.match(f"^{self.word_pattern}$", words[0]):
                    word = words[0]
            case 2:
                if re.match(f"^{self.phonetics_pattern}$", words[1]):
                    word = words[0]

        return word

    def _get_split_phonetics_line(self) -> list:
        try:
            phonetics_line = self._get_line(1)
        except IndexError:
            return []
        return phonetics_line.split(" ")

    def _get_raw_phonetics(self) -> str | None:
        phonetics_from_answer_line = None
        split_phonetics_line = self._get_split_phonetics_line()
        phonetics_from_phonetics_line = self._filter_phonetics_from(
            split_phonetics_line)

        if not phonetics_from_phonetics_line:
            phonetics_from_answer_line = self._get_phonetics_from_answer_line()

        phonetics = (phonetics_from_phonetics_line
                     or phonetics_from_answer_line or None)

        # [1:-1] cuts brackets
        return phonetics[1:-1] if phonetics is not None else phonetics

    def _filter_phonetics_from(self, words: list) -> str | None:
        """
        Filters list entries matching the phonetics pattern and returns a first
        match if pattern is found.
        """
        filtered_phonetics = list(filter(lambda word:
                                         re.match(self.phonetics_pattern,
                                                  word), words))
        phonetics = next(iter(filtered_phonetics), None)
        return phonetics

    def _get_phonetics_from_answer_line(self) -> str | None:
        matched_phonetics = re.findall(self.phonetics_pattern,
                                       self._get_line(0))
        if matched_phonetics:
            return matched_phonetics[0]
        return None

    def _get_formatted_phonetics(self) -> str | None:
        raw_phonetics = self.raw_phonetics
        formatted_phonetics = None
        if raw_phonetics is not None:
            formatted_phonetics = PhoneticsConverter(
                self.raw_phonetics).converted_phonetics
        return formatted_phonetics

    def _get_example_sentences(self) -> list:
        if self.phonetics_key:
            starting_line = 2
        else:
            starting_line = 1
        sentences = self._strip_media_tags(self.side_contents)
        split_sentences = sentences.splitlines()[starting_line:]

        return self._clean_sentences(split_sentences)

    @property
    def _clean_sentences(self):
        functions = [
            list,
            lambda lines: map(lambda line: self._merge_characters(
                " ", line), lines),
            lambda lines: map(
                lambda lns: self.strip_tags_except_specific(lns), lines)
        ]

        return compose(*functions)

    def _get_output_text(self) -> str:
        phonetics_key = (f'<span class="phonetic-key">'
                         f'{self.phonetics_key}</span>'
                         if self.phonetics_key else None)
        phonetics = (f'<span class="phonetic-spelling">'
                     f'[{self.formatted_phonetics}]'
                     f'</span>' if self.raw_phonetics else None)

        def get_phonetics_component():
            component = None
            if phonetics_key and phonetics:
                component = (f'<div class="phonetics">{phonetics_key} '
                             f'{phonetics}</div>')
            elif phonetics_key:
                component = f'<div class="phonetics">{phonetics_key}</div>'
            return component

        def get_answer_component():
            if not phonetics_key and phonetics:
                output = (f'<div class="answer">{self.answer} '
                          + phonetics + '</div>')
            else:
                output = f'<div class="answer">{self.answer}</div>'
            return output

        answer = get_answer_component()
        phonetics_component = get_phonetics_component()
        sentences = "".join(f"<p><span>{sentence}</span></p>"
                            for sentence in self.example_sentences)
        example_sentences = (
            f'<div class=”answer-example-sentences”>{sentences}</div>'
            if sentences else None)
        answer_components = [answer, phonetics_component, example_sentences]

        return "".join(filter(None, answer_components))

    def _get_answer(self):
        answer_line = self._get_line(0)
        answer_line_split = re.split(self.phonetics_pattern, answer_line)
        return answer_line_split[0].strip()

    answer = property(_get_answer,
                      doc="The main answer is usually located in"
                          " the first line of an answer side"
                          " of a card.")
    phonetics_key = property(_get_phonetics_key)
    raw_phonetics = property(_get_raw_phonetics)
    formatted_phonetics = property(_get_formatted_phonetics)
    example_sentences = property(_get_example_sentences)
