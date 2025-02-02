"""
Classes representing an 'Item's Side' (question and answer). Contains abstract
class with methods/fields common for both question and answer as well
as method/field signatures implemented in concrete classes.
"""

import os
from xml.etree import ElementTree as ET

import re

from bs4 import BeautifulSoup


class CardSide:
    """
    Abstract class for Item's question/answer (fields common
    for both inheriting classes).
    """

    def __init__(self, side_contents):
        self.side_contents = side_contents

    @staticmethod
    def strip_tags_except_specific(text: str) -> str:
        # from: https://stackoverflow.com/questions/56001921/
        # removing-tags-from-html-except-specific-ones-but-keep-their-contents
        # original author: glhr
        soup = BeautifulSoup(text, "html.parser")
        for e in soup.find_all():
            if e.name not in ["strike", "i"]:
                e.unwrap()
        return str(soup)

    def _get_tag_contents(self, tag) -> str | None:
        """
        Extracts a path as it is embedded in the elements.xml file (which
        contains only relative paths to media files) - without expanding it
        into an absolute path.
        """
        tag_contents = ET.fromstring(
            f"<root>{self.side_contents}</root>").find(tag)
        if tag_contents is not None:
            return tag_contents.text

    @staticmethod
    def _get_filename(file_path) -> str | None:
        if file_path is not None:
            return os.path.basename(file_path)

    @staticmethod
    def _strip_media_tags(text: str) -> str:
        # media tags in elements.xml are always appended
        # to the end of the field
        pattern = "<img>|<snd>"
        output = re.split(pattern, text)
        return output[0]

    def _get_output_text(self) -> str:
        """
        Output in html or other format - depending on implementation in
        inheriting classes.
        """
        pass

    image_file_path = property(lambda self: self._get_tag_contents("img"))
    sound_file_path = property(lambda self: self._get_tag_contents("snd"))
    image_file_name = property(lambda self: self._get_filename(
        self.image_file_path))
    sound_file_name = property(lambda self: self._get_filename(
        self.sound_file_path))

    # otherwise doesn't work with inheriting classes
    output_text = property(lambda self: self._get_output_text())


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
        merged_question = self._merge_question()
        output = self._format_placeholder(merged_question)
        return self._highlight_text_in_brackets(output)

    def _merge_question(self):
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


class Answer(CardSide):
    def __init__(self, answer):
        """
        answer - content of <item><a></a></item> tags.
        """
        super().__init__(answer)

    def _get_answer(self) -> str:
        pass

    def _get_phonetics_key(self) -> str:
        pass

    def _get_phonetics(self) -> str:
        pass

    def _get_example_sentences(self) -> str:
        pass

    answer = property(_get_answer, doc="Answer is usually located in"
                                       " the first line of an answer side"
                                       " of a card.")
    phonetics_key = property(_get_phonetics_key)
    phonetics = property(_get_phonetics)
    example_sentences = property(_get_example_sentences)
