from xml.etree.ElementTree import Element

class Item:
    """
    Processes a single 'Item' (<item></item>) from the elements.xml file.
    """
    def __init__(self, item: Element):
        pass

    @property
    def question(self) -> str:
        pass

    @property
    def answer(self) -> str:
        pass

    @property
    def review_details(self) -> dict:
        pass
