from typing import Any
from xml.etree.ElementTree import Element

class Item:
    """
    Processes a single 'Item' (<item></item>) from the elements.xml file.
    """
    def __init__(self, item: Element):
        self._item_element = item

    @property
    def question(self) -> str:
        return self._item_element.find("q").text

    @property
    def answer(self) -> str:
        return self._item_element.find("a").text

    @property
    def review_details(self) -> dict:
        return self._item_element.attrib

    @staticmethod
    def keys() -> list[str]:
        return ["question", "answer", "review_details"]

    def values(self) -> list[Any]:
        return [self.question, self.answer, self.review_details]

    def __getitem__(self, key):
        return dict(zip(self.keys(), self.values()))[key]
