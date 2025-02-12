import re

from cards.management.fr_importer.modules.card_side import CardSide
from cards.utils.helpers import compose


class Question(CardSide):
    def __init__(self, question):
        """
        question - contents of <item><q></q></item> (without <q></q> tags).
        """
        super().__init__(question)

    def _get_example(self) -> str:
        get_example = compose(
            "<br/>".join,
            lambda acc: filter(None, acc.split("\n")[1:]))
        return get_example(self.side_contents)

    @staticmethod
    def _highlight_text_in_brackets(text: str) -> str:
        def replace_text_in_brackets(matched_text):
            return ('<span class="highlighted-text">'
                    f'{matched_text.group(0)}'
                    '</span>')

        pattern = "\[[\w\s]+\]"
        return re.sub(pattern, replace_text_in_brackets, text)

    @staticmethod
    def _format_placeholder(text: str) -> str:
        """
        Adds html formatting to the '[...]' placeholder.
        """
        formatted_placeholder = ('<span class="extracted-text" '
                                 'title="guess the missing part">'
                                 '[&hellip;]</span>')
        return re.sub("\[...\]|\[…\]", formatted_placeholder, text)

    def _get_output_text(self) -> str:
        block = [self.definition_block, self.question_example_separating_hr,
                 self.example_block]
        merged_question = "".join(filter(None, block))
        output = self._format_placeholder(merged_question)
        return self._highlight_text_in_brackets(output)

    definition = property(lambda self: self._get_line(0))
    definition_block = property(
        lambda self: '<div class="card-question-definition">'
                     f'<p>{self.definition}</p>'
                     '</div>')
    example = property(_get_example)
    example_block = property(lambda self: '<div class="card-question-example">'
                                          f'<p>{self.example}</p>'
                                          '</div>' if self.example else None)
    # This one should appear only if example is present
    question_example_separating_hr = property(
        lambda self: '<hr class="question-example-separating-hr"/>'
        if self.example else None)
