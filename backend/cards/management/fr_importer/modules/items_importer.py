from xml.etree.ElementTree import Element

from cards.management.fr_importer.modules.html_memorized_card import \
    HtmlFormattedMemorizedCard
import xml.etree.ElementTree as ET

from cards.management.fr_importer.modules.item import Item


class ItemsImporter:
    Card = HtmlFormattedMemorizedCard

    def __init__(self, path):
        self._import_xpath = None
        tree = ET.parse(path)
        self._root = tree.getroot()

    @property
    def _starting_node(self) -> Element:
        if self._import_xpath is None:
            return self._root
        else:
            return self._root.find(self._import_xpath)

    def set_import_xpath(self, path: str|None):
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
            formatted_card = self.Card(Item(item_element), self.time_of_start)
            yield formatted_card
