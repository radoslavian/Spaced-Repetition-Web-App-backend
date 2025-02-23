"""
Classes representing an 'Item's Side' (question and answer). Contains abstract
class with methods/fields common for both question and answer as well
as method/field signatures implemented in concrete classes.
"""

from os import path, PathLike
from xml.etree import ElementTree as ET
import re

from bs4 import BeautifulSoup

from cards.utils.helpers import compose


class CardSide:
    """
    Abstract class for Item's question/answer (fields common
    for both inheriting classes).
    """

    def __init__(self, side_contents: str):
        if not side_contents:
            raise ValueError("no side content was provided")
        self.output_block = []
        self._expanding_path = None
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

    def _get_examples(self, from_line=1) -> list[str]:
        return list(filter(None, self.side_contents.splitlines()[from_line:]))

    @staticmethod
    def _get_filename(file_path) -> str | None:
        if file_path is not None:
            return path.basename(file_path)

    @staticmethod
    def _strip_media_tags(text: str) -> str:
        # media tags in elements.xml are always appended
        # to the end of the field
        pattern = "<img>|<snd>"
        output = re.split(pattern, text)
        return output[0]

    def _get_line(self, index) -> str | None:
        split_contents = self.side_contents.splitlines()
        try:
            line = split_contents[index]
        except IndexError:
            return None
        if len(split_contents) < 2 and split_contents[0] == "":
            raise ValueError("The side appears to be empty!")

        return line

    @staticmethod
    def _merge_characters(character: str, text: str) -> str:
        pattern = f"{character}" + "{2,}"
        return re.sub(pattern, lambda matched_text: character, text)

    @property
    def output_text(self) -> str:
        """
        Outputs text in html or other format - depending on implementation in
        inheriting classes.
        """
        return "".join(filter(None, self.output_block))

    _clean_contents = lambda self, original_contents: compose(
        lambda acc: self._merge_characters(" ", acc),
        self._strip_tags_except_specific,
        self._strip_media_tags)(original_contents)

    @property
    def expanding_path(self) -> str|PathLike|None:
        return self._expanding_path

    @expanding_path.setter
    def expanding_path(self, file_path: str | PathLike):
        self._expanding_path = file_path

    @property
    def side_contents(self):
        return self._clean_contents(self._original_side_contents)

    @staticmethod
    def keys():
        return ["output_text", "image_file_path", "image_file_name",
                "sound_file_path", "sound_file_name"]

    def values(self):
        return [self.output_text, self.image_file_path,
                self.image_file_name, self.sound_file_path,
                self.sound_file_name]

    def __getitem__(self, key):
        return dict(zip(self.keys(), self.values()))[key]

    @property
    def image_file_path(self):
        return self._get_expanded_path_from_tag("img")

    @property
    def sound_file_path(self):
        return self._get_expanded_path_from_tag("snd")

    def _get_filepath_from_tag(self, tag: str) -> str|None:
        return self._get_tag_contents(tag)

    def _get_expanded_path_from_tag(self, tag:str) -> str|None:
        """
        Returns path expanded with expanding_path component (if that component
        is set), otherwise returns unexpanded path.
        """
        file_path = self._get_filepath_from_tag(tag)
        if self.expanding_path and file_path is not None:
            return path.join(self.expanding_path, file_path)
        return file_path

    image_file_name = property(lambda self: self._get_filename(
        self.image_file_path))
    sound_file_name = property(lambda self: self._get_filename(
        self.sound_file_path))
