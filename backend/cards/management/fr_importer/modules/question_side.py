import re

from cards.management.fr_importer.modules.card_side import CardSide
from cards.utils.helpers import compose


class Question(CardSide):
    def __init__(self, question):
        """
        question - contents of <item><q></q></item> (without <q></q> tags).
        """
        super().__init__(question)

    def _get_definition(self) -> str:
        get_output = compose(
            lambda acc: self._merge_characters(" ", acc),
            self.strip_tags_except_specific,
            self._strip_media_tags
        )
        return get_output(self.side_contents.split("\n")[0])

    def _get_example(self) -> str:
        get_example = compose(
            lambda acc: self._merge_characters(" ", acc),
            "<br/>".join,
            lambda acc: filter(None, acc.split("\n")[1:]),
            self.strip_tags_except_specific,
            self._strip_media_tags,
        )
        return get_example(self.side_contents)

    @staticmethod
    def _merge_characters(character: str, text: str) -> str:
        pattern = f"{character}" + "{2,}"
        return re.sub(pattern, lambda matched_text: character, text)

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
        merged_question = self._merge_question_components()
        output = self._format_placeholder(merged_question)
        return self._highlight_text_in_brackets(output)

    def _merge_question_components(self):
        definition = ('<div class="card-question-definition">'
                      f'<p>{self.definition}</p>'
                      '</div>')
        hr = ('<hr class="question-example-separating-hr"/>'
              if self.example else None)
        example = ('<div class="card-question-example">'
                   f'<p>{self.example}</p>'
                   '</div>') if self.example else None
        merged_question = "".join(filter(None, [definition, hr, example]))
        return merged_question

    definition = property(_get_definition)
    example = property(_get_example)
