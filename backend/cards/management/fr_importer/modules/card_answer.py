import re

from cards.management.fr_importer.modules.card_side import CardSide
from cards.management.fr_importer.modules.phonetics_converter import \
    PhoneticsConverter


class Answer(CardSide):
    def __init__(self, answer):
        """
        answer - content of <item><a></a></item> tags.
        """
        super().__init__(answer)
        self.phonetics_pattern = r"\[[\w\d'^_\-():]+]"
        self.word_pattern = "[\w.,?-]+"

    def _get_phonetics_key(self) -> str|None:
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
        words = self._get_split_phonetics_line()
        if not words:
            phonetics = self._get_phonetics_from_answer_line()
        else:
            phonetics = self._filter_phonetics_from(words)

        #[1:-1] cuts brackets
        return phonetics[1:-1] if phonetics is not None else phonetics

    def _filter_phonetics_from(self, words:list) -> str|None:
        """
        Filters list entries matching the phonetics pattern and returns a first
        match if pattern is found.
        """
        filtered_phonetics = list(filter(lambda word:
                                         re.match(self.phonetics_pattern,
                                                  word), words))
        phonetics = next(iter(filtered_phonetics), None)
        return phonetics

    def _get_phonetics_from_answer_line(self) -> str|None:
        matched_phonetics = re.findall(self.phonetics_pattern,
                                       self._get_line(0))
        if matched_phonetics:
            return matched_phonetics[0]
        return None

    def _get_formatted_phonetics(self) -> str|None:
        raw_phonetics = self.raw_phonetics
        formatted_phonetics = None
        if raw_phonetics is not None:
            formatted_phonetics = PhoneticsConverter(
                self.raw_phonetics).converted_phonetics
        return formatted_phonetics

    def _get_example_sentences(self) -> str:
        pass

    def _get_output_text(self) -> str:
        pass

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
