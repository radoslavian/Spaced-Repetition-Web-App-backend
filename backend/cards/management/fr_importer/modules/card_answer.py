import re
from gc import is_finalized

from cards.management.fr_importer.modules.card_side import CardSide
from cards.management.fr_importer.modules.phonetics_converter import \
    PhoneticsConverter


class Answer(CardSide):
    def __init__(self, answer):
        """
        answer - content of <item><a></a></item> tags.
        """
        super().__init__(answer)
        self.phonetics_pattern = r"\[.+\]"

    def _get_phonetics_key(self) -> str | None:
        matched_line = self._match_phonetics_line(1)
        return matched_line["remaining_text"]

    def _match_phonetics_line(self, line_index) -> dict:
        single_word = "^[^\s.]{2,30}$"
        phonetics_line = self._get_line(line_index)
        extracted_output = {"phonetics": None,
                            "remaining_text": None}
        if phonetics_line:
            matched_phonetics = re.search(
                self.phonetics_pattern, phonetics_line)
            if matched_phonetics:
                extracted_output["phonetics"] = matched_phonetics.group(0)
                # pattern cuts phonetics and a redundant space
                remaining_text = re.sub(f"\s{2,}?{self.phonetics_pattern}",
                                    "",
                                    phonetics_line)
                if remaining_text:
                    extracted_output["remaining_text"] = remaining_text.strip()
            elif re.match(single_word, phonetics_line):
                extracted_output["remaining_text"] = phonetics_line

        return extracted_output

    def _get_raw_phonetics(self) -> str | None:
        phonetics_in_answer_line = None
        output_phonetics = None
        phonetics_in_phonetics_line = \
            self._match_phonetics_line(1)["phonetics"]

        if not phonetics_in_phonetics_line:
            phonetics_in_answer_line = self._get_phonetics_from_answer_line()

        phonetics = (phonetics_in_phonetics_line
                     or phonetics_in_answer_line or None)

        if phonetics:
            # [1:-1] cuts brackets
            output_phonetics = phonetics[1:-1]

        return output_phonetics

    def _get_phonetics_from_answer_line(self) -> str | None:
        matched_phonetics = re.findall(self.phonetics_pattern,
                                       self._get_line(0))
        if matched_phonetics:
            return matched_phonetics[0]
        return None

    def _get_formatted_phonetics_spelling(self) -> str | None:
        raw_phonetics = self.raw_phonetics_spelling
        formatted_phonetics = None
        if raw_phonetics is not None:
            formatted_phonetics = PhoneticsConverter(
                self.raw_phonetics_spelling).converted_phonetics
        return formatted_phonetics

    def _get_example_sentences(self) -> list:
        if self.phonetics_key:
            starting_line = 2
        else:
            starting_line = 1
        split_sentences = self.side_contents.splitlines()[starting_line:]

        return split_sentences

    @property
    def output_text(self) -> str:
        answer_side = [self.answer_block, self.phonetics_block,
                       self.example_sentences_block]
        return "".join(filter(None, answer_side))

    def _get_example_sentences_block(self):
        example_sentences = "".join(f"<p><span>{sentence}</span></p>"
                                    for sentence in self.example_sentences)
        example_sentences_block = (
            f'<div class=”answer-example-sentences”>{example_sentences}</div>'
            if example_sentences else None)
        return example_sentences_block

    def _get_phonetics_block(self):
        phonetics_block = None
        if self.phonetics_key and self.raw_phonetics_spelling:
            phonetics_block = (
                f'<div class="phonetics">{self.phonetics_key_block} '
                f'{self.phonetics_spelling_block}</div>')
        elif self.phonetics_key:
            phonetics_block = (f'<div class="phonetics">'
                               f'{self.phonetics_key_block}</div>')
        return phonetics_block

    def _get_answer_block(self):
        if not self.phonetics_key and self.raw_phonetics_spelling:
            output = (f'<div class="answer">{self.answer} '
                      + f"{self.phonetics_spelling_block}</div>")
        else:
            output = f'<div class="answer">{self.answer}</div>'
        return output

    def _get_answer(self):
        phonetics_pattern = f"{self.phonetics_pattern}\s?"
        answer_line = self._get_line(0)
        no_phonetics = re.sub(phonetics_pattern, "", answer_line)
        return no_phonetics.strip()

    answer = property(_get_answer,
                      doc="The main answer is usually located in"
                          " the first line of an answer side"
                          " of a card.")
    answer_block = property(_get_answer_block)
    phonetics_key = property(_get_phonetics_key)
    phonetics_key_block = property(lambda self:
                                   f'<span class="phonetic-key">'
                                   f'{self.phonetics_key}</span>'
                                   if self.phonetics_key else None)
    raw_phonetics_spelling = property(_get_raw_phonetics)
    formatted_phonetics_spelling = property(_get_formatted_phonetics_spelling)
    phonetics_spelling_block = property(lambda self:
                                        f'<span class="phonetic-spelling">'
                                        f'[{self.formatted_phonetics_spelling}]'
                                        f'</span>' if self.raw_phonetics_spelling else None)
    phonetics_block = property(_get_phonetics_block)
    example_sentences = property(_get_example_sentences)
    example_sentences_block = property(_get_example_sentences_block)
