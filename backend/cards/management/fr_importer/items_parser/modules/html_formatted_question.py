import re

from cards.management.fr_importer.items_parser.modules.card_question import Question
from cards.utils.helpers import compose


class HTMLFormattedQuestion(Question):
    def __init__(self, question):
        super().__init__(question)
        self.output_block = [self.definition,
                             self.question_example_separating_hr,
                             self.examples_block]

    _format_text = lambda self, side_contents: compose(
        self._change_characters_in_text,
        self._highlight_text_in_brackets
    )(side_contents)

    @staticmethod
    def _change_characters_in_text(text: str):
        characters = [("...", "&hellip;")]
        new_text = text[:]
        for character in characters:
            new_text = new_text.replace(character[0], character[1])
        return new_text

    @property
    def side_contents(self):
        return self._format_text(super().side_contents)

    @property
    def definition(self) -> str:
        return ('<div class="card-question-definition">'
                f'<p>{super().definition}</p>'
                f'</div>')

    @property
    def examples(self) -> list[str]:
        return [f"<p>{example}</p>" for example
                in super().examples]

    @property
    def examples_block(self) -> str | None:
        return ('<div class="card-question-example">'
                + "".join(self.examples)
                + '</div>' if self.examples else None)

    question_example_separating_hr = property(
        lambda self: '<hr class="question-example-separating-hr"/>'
        if super().examples else None)

    @staticmethod
    def _highlight_text_in_brackets(text: str) -> str:
        def replace_text_in_brackets(matched_text):
            return ('<span class="highlighted-text">'
                    f'{matched_text.group(0)}'
                    '</span>')

        pattern = "\[[\w\s\.-]+\]"
        return re.sub(pattern, replace_text_in_brackets, text)
