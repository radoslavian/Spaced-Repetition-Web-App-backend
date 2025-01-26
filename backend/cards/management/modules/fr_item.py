from cards.management.modules.fr_item_side import ItemQuestion, ItemAnswer


class Item:
    """
    Processes a single 'Item' (<item></item>) from the elements.xml file.
    """

    def __init__(self, item):
        pass

    def _extract_question(self):
        pass

    def _extract_answer(self):
        pass

    def _get_question(self) -> ItemQuestion:
        pass

    def _get_answer(self) -> ItemAnswer:
        pass

    question = property(_get_question)
    answer = property(_get_answer)
