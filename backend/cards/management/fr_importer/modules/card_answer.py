import re

from cards.management.fr_importer.modules.card_side import CardSide


class Answer(CardSide):
    def __init__(self, answer):
        """
        answer - content of <item><a></a></item> tags.
        """
        super().__init__(answer)
        self.phonetics_pattern = "^\[[\w\d'^_\-():]+]$"

    def _get_phonetics_key(self) -> str|None:
        words = self._get_split_phonetics_line()
        if not words:
            return
        word = self._match_phonetics_key(words)

        return word

    def _match_phonetics_key(self, words: list) -> str | None:
        word_pattern = "^[\w.,?-]+$"
        word = None
        match len(words):
            case 1:
                if re.match(word_pattern, words[0]):
                    word = words[0]
            case 2:
                if re.match(self.phonetics_pattern, words[1]):
                    word = words[0]

        return word

    def _get_split_phonetics_line(self) -> list:
        try:
            phonetics_line = self._get_line(1)
        except IndexError:
            return []
        return phonetics_line.split(" ")

    def _get_example_sentences(self) -> str:
        pass

    def _get_phonetics(self) -> str:
        pass

    def _get_formatted_phonetics(self) -> str:
        pass

    def _get_output_text(self) -> str:
        pass

    answer = property(lambda self: self._get_line(0),
                      doc="Main answer is usually located in"
                          " the first line of an answer side"
                          " of a card.")
    phonetics_key = property(_get_phonetics_key)
    phonetics = property(_get_phonetics)
    formatted_phonetics = property(_get_formatted_phonetics)
    example_sentences = property(_get_example_sentences)
