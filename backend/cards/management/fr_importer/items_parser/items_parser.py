import os.path
from os import PathLike
from xml.etree.ElementTree import Element

from cards.management.fr_importer.items_parser.modules.html_memorized_card import \
    HtmlFormattedMemorizedCard
from cards.management.fr_importer.items_parser.modules.item import Item
from cards.utils.xml_parser import parse


class ItemsParser:
    Card = HtmlFormattedMemorizedCard

    def __init__(self, path):
        self._original_path = path
        self._import_xpath = None
        tree = parse(path)
        self._root = tree.getroot()

    @property
    def dirname(self) -> str|PathLike:
        """
        Directory name of the file from which items are imported.
        """
        return os.path.dirname(self._original_path)

    @property
    def _starting_node(self) -> Element:
        if self._import_xpath is None:
            return self._root
        else:
            return self._root.find(self._import_xpath)

    @property
    def import_xpath(self) -> str|None:
        return self._import_xpath

    @import_xpath.setter
    def import_xpath(self, path: str|None):
        if path is not None and self._root.find(path) is None:
            raise ValueError(f"Given path: {path} was not found.")
        else:
            self._import_xpath = path

    @property
    def time_of_start(self) -> int:
        return int(self._root.attrib["time_of_start"])

    @property
    def items(self):
        return self._starting_node.iter("item")

    def __iter__(self):
        for item_element in self.items:
            card = self.Card(Item(item_element), self.time_of_start)
            card.expanding_path = self.dirname
            yield card
