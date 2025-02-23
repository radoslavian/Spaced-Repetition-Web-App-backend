from cards.management.fr_importer.items_parser.modules.card_answer import Answer
from cards.management.fr_importer.items_parser.modules.phonetics_converter import \
    PhoneticsConverter


class HTMLFormattedAnswer(Answer):
    def __init__(self, answer):
        super().__init__(answer)
        self.output_block = [self.answer, self.phonetics_block,
                             self.example_sentences_block]

    @property
    def phonetics_key(self) -> str | None:
        return ('<span class="phonetic-key">'
                f'{super().phonetics_key}'
                '</span>' if super().phonetics_key else None)

    @property
    def phonetics_block(self) -> str | None:
        phonetics_block = None
        if self.phonetics_key and self.phonetics_spelling:
            phonetics_block = (
                f'<div class="phonetics">{self.phonetics_key} '
                f'{self.phonetics_spelling_block}</div>')
        elif self.phonetics_key:
            phonetics_block = (f'<div class="phonetics">'
                               f'{self.phonetics_key}</div>')
        return phonetics_block

    @property
    def phonetics_spelling(self) -> str | None:
        raw_phonetics = super().phonetics_spelling
        formatted_phonetics = None
        if raw_phonetics is not None:
            formatted_phonetics = PhoneticsConverter(
                raw_phonetics).converted_phonetics
        return formatted_phonetics

    @property
    def phonetics_spelling_block(self) -> str:
        return (f'<span class="phonetic-spelling">'
                f'[{self.phonetics_spelling}]'
                f'</span>' if self.phonetics_spelling else None)

    @property
    def answer(self) -> str:
        answer_div = '<div class="answer">{answer}</div>'
        if not self.phonetics_key and self.phonetics_spelling:
            output = (super().answer + " "
                      + f"{self.phonetics_spelling_block}")
        else:
            output = super().answer
        return answer_div.format(answer=output)

    @property
    def example_sentences(self) -> list[str]:
        return [f"<p><span>{sentence}</span></p>"
                for sentence in super().example_sentences]

    @property
    def example_sentences_block(self):
        example_sentences_block = (
            '<div class=”answer-example-sentences”>'
            + "".join(self.example_sentences)
            + '</div>'
            if super().example_sentences else None)
        return example_sentences_block
