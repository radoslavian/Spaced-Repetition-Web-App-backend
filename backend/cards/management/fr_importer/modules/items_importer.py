from xml.etree.ElementTree import Element

from cards.management.fr_importer.modules.html_memorized_card import \
    HtmlFormattedMemorizedCard
import xml.etree.ElementTree as ET


class ItemsImporter:
    Card = HtmlFormattedMemorizedCard

    def __init__(self, path):
        self._path = path
        self._tree = ET.parse(path)
        self._root = self._tree.getroot()

    @property
    def time_of_start(self) -> int:
        return int(self._root.attrib["time_of_start"])

    @property
    def items(self):
        return self._root.iter("item")

    def __iter__(self):
        for item in self.items:
            formatted_card = self.convert_item_to_card(item)
            yield formatted_card

    def convert_item_to_card(self, item: Element) \
            -> HtmlFormattedMemorizedCard:
        data = {
            "question": item.find("q").text,
            "answer": item.find("a").text,
            "review_details": item.attrib
        }
        return self.Card(data, self.time_of_start)
