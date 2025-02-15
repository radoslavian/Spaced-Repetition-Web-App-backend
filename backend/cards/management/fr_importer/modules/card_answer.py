import re

from cards.management.fr_importer.modules.card_side import CardSide


class Answer(CardSide):
    def __init__(self, answer):
        """
        answer - content of <item><a></a></item> tags.
        """
        super().__init__(answer)
        self.phonetics_pattern = r"\[.+\]"

    @property
    def phonetics_key(self) -> str | None:
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

    def _get_answer(self):
        phonetics_pattern = f"{self.phonetics_pattern}\s?"
        answer_line = self._get_line(0)
        no_phonetics = re.sub(phonetics_pattern, "", answer_line)
        return no_phonetics.strip()

    answer = property(_get_answer,
                      doc="The main answer is usually located in"
                          " the first line of an answer side"
                          " of a card.")

    @property
    def example_sentences(self) -> list[str]:
        if self.phonetics_key:
            starting_line = 2
        else:
            starting_line = 1
        return super()._get_examples(starting_line)

    raw_phonetics_spelling = property(_get_raw_phonetics)
