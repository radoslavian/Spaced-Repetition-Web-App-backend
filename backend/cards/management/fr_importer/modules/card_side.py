"""
Classes representing an 'Item's Side' (question and answer). Contains abstract
class with methods/fields common for both question and answer as well
as method/field signatures implemented in concrete classes.
"""

import os
from xml.etree import ElementTree as ET
import re

from bs4 import BeautifulSoup

from cards.utils.helpers import compose


class CardSide:
    """
    Abstract class for Item's question/answer (fields common
    for both inheriting classes).
    """

    def __init__(self, side_contents):
        self._original_side_contents = side_contents

    @staticmethod
    def _strip_tags_except_specific(text: str) -> str:
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
            f"<root>{self._original_side_contents}</root>").find(tag)
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

    def _get_line(self, index) -> str:
        split_contents = self.side_contents.split("\n")
        line = split_contents[index]
        if len(split_contents) < 2 and split_contents[0] == "":
            raise ValueError("The side appears to be empty!")

        return line

    @staticmethod
    def _merge_characters(character: str, text: str) -> str:
        pattern = f"{character}" + "{2,}"
        return re.sub(pattern, lambda matched_text: character, text)

    def _get_output_text(self) -> str:
        """
        Output in html or other format - depending on implementation in
        inheriting classes.
        """
        pass

    @property
    def side_contents(self):
        functions = [lambda acc: self._merge_characters(" ", acc),
            self._strip_tags_except_specific,
            self._strip_media_tags]
        clean_contents = compose(*functions)

        return clean_contents(self._original_side_contents)

    image_file_path = property(lambda self: self._get_tag_contents("img"))
    sound_file_path = property(lambda self: self._get_tag_contents("snd"))
    image_file_name = property(lambda self: self._get_filename(
        self.image_file_path))
    sound_file_name = property(lambda self: self._get_filename(
        self.sound_file_path))

    # otherwise doesn't work with inheriting classes
    output_text = property(lambda self: self._get_output_text())


