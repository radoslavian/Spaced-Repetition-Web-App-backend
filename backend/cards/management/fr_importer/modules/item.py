from cards.management.fr_importer.modules.card_answer import Answer
from cards.management.fr_importer.modules.question_side import Question


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

    def _get_question(self) -> Question:
        pass

    def _get_answer(self) -> Answer:
        pass

    question = property(_get_question)
    answer = property(_get_answer)
