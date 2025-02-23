from cards.management.fr_importer.modules.html_formatted_answer import \
    HTMLFormattedAnswer
from cards.management.fr_importer.modules.html_formatted_question import \
    HTMLFormattedQuestion
from cards.management.fr_importer.modules.item import Item


class HtmlFormattedCard:
    """
    Representation of a not yet memorized (pending) card.
    """

    def __init__(self, pending_card: dict|Item):
        if not pending_card["question"] or not pending_card["answer"]:
            raise ValueError("missing obligatory argument: question_text or"
                             "answer_text")
        self._expanding_path = None
        self._question = HTMLFormattedQuestion(pending_card["question"])
        self._answer = HTMLFormattedAnswer(pending_card["answer"])

    @property
    def expanding_path(self) -> str|None:
        return self._expanding_path

    @expanding_path.setter
    def expanding_path(self, file_path):
        self._expanding_path = \
            self._question.expanding_path \
            = self._answer.expanding_path \
            = file_path

    @property
    def question_output_text(self):
        return self._question.output_text

    @property
    def answer_output_text(self):
        return self._answer.output_text

    def __getitem__(self, key):
        return dict(zip(self.keys(), self.values()))[key]

    @staticmethod
    def keys():
        return ["question", "answer"]

    def values(self):
        return [dict(field) for field in (self._question, self._answer,)]
