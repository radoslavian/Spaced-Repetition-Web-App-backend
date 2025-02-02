import re

from cards.management.fr_importer.modules.card_side import CardSide


class Question(CardSide):
    def __init__(self, question):
        """
        question - contents of <item><q></q></item> (without <q></q> tags).
        """
        super().__init__(question)

    def _get_definition(self) -> str:
        first_line = self.side_contents.split("\n")[0]
        definition = self._strip_media_tags(first_line)
        filtered_tags = self.strip_tags_except_specific(definition)
        merged_spaces = self._merge_characters(" ", filtered_tags)
        return merged_spaces

    def _get_example(self) -> str:
        contents_no_tags = self.strip_tags_except_specific(
            self._strip_media_tags(self.side_contents))
        # split and filter empty lines
        split_examples = filter(None, contents_no_tags.split("\n")[1:])
        examples = "<br/>".join(split_examples)
        merged_spaces = self._merge_characters(" ", examples)
        return merged_spaces

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
