from xml.etree.ElementTree import Element

from cards.management.fr_importer.modules.html_memorized_card import \
    HtmlFormattedMemorizedCard
import xml.etree.ElementTree as ET


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
        for item in self.items:
            formatted_card = self._convert_item_to_card(item)
            yield formatted_card

    def _convert_item_to_card(self, item: Element) -> Card:
        data = {
            "question": item.find("q").text,
            "answer": item.find("a").text,
            "review_details": item.attrib
        }
        return self.Card(data, self.time_of_start)
