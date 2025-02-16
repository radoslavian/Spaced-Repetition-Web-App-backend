from cards.management.fr_importer.modules.html_formatted_answer import \
    HTMLFormattedAnswer
from cards.management.fr_importer.modules.html_formatted_question import \
    HTMLFormattedQuestion


class HtmlFormattedCard:
    def __init__(self, question_text, answer_text):
        if not question_text or not answer_text:
            raise ValueError("missing obligatory argument: question_text or"
                             "answer_text")
        self._question = HTMLFormattedQuestion(question_text)
        self._answer = HTMLFormattedAnswer(answer_text)

    @property
    def question_output_text(self):
        return self._question.output_text

    @property
    def answer_output_text(self):
        return self._answer.output_text

    @staticmethod
    def keys():
        return ["question", "answer"]

    def __getitem__(self, key):
        values = [dict(field) for field in (self._question, self._answer,)]
        return dict(zip(self.keys(), values))[key]