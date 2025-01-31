"""
Classes representing an 'Item's Side' (question and answer). Contains abstract
class with methods/fields common for both question and answer as well
as method/field signatures implemented in concrete classes.
"""

import os
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup
from django.utils.html import strip_tags


class CardSide:
    """
    Abstract class for Item's question/answer (fields common
    for both inheriting classes).
    """
    def __init__(self, side_contents):
        self.side_contents = side_contents

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
    output_text = property(_get_output_text)


class Question(CardSide):
    def __init__(self, question):
        """
        question - contents of <item><q></q></item> (without <q></q> tags).
        """
        super().__init__(question)

    @staticmethod
    def _remove_media_tags(text:str) -> str:
        media_tags = ["img", "snd"]

        # surrounding text with whatever top-level markup is necessary !
        # otherwise get_text will return no text at all !!!
        soup = BeautifulSoup(f"<root>{text}</root>", "lxml-xml")

        for media_tag in media_tags:
            for tag in soup.find_all(media_tag):
                tag.decompose()

        return soup.get_text("<br/>")


    def _get_definition(self) -> str:
        full_definition = self.side_contents.split("\n")[0]
        definition = self._remove_media_tags(full_definition)
        return definition

    def _get_example(self) -> str:
        # how is that it works?
        full_example = "<br/>".join(self.side_contents.split("\n")[1:])
        example = self._remove_media_tags(full_example)
        return example

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
