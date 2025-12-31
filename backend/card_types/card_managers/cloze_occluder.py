from bs4 import BeautifulSoup


class ClozeOccluder:
    occluded_question = '[...]'
    occluded_gap = '{...}'
    answer_template = '[{}]'

    def __init__(self, description_text):
        self.bs = BeautifulSoup(description_text, features="lxml")
        self.clozes = self.bs.findAll("cloze")
        self._check_for_id_collisions()

    def _check_for_id_collisions(self):
        """
        Raises an exception if there are several cloze ids with the same value.
        """
        cloze_ids = self._get_cloze_ids()
        for cloze_id in cloze_ids:
            cloze_id_count = cloze_ids.count(cloze_id)
            if cloze_id_count > 1:
                exception_message = ('<cloze> id collision detected: '
                                     'the "{0}" count is "{1}"')
                raise ValueError(exception_message.format(cloze_id,
                                                          cloze_id_count))

    def _get_cloze_ids(self):
        try:
            clozes = [cloze["id"] for cloze in self.clozes]
        except KeyError:
            raise KeyError("One or more clozes has no id.")
        return clozes

    def get_cards(self):
        return [self._get_card_details_for_cloze(cloze)
                for cloze in self.clozes]

    def _get_card_details_for_cloze(self, cloze):
        question = BeautifulSoup(str(self.bs), features="lxml")
        answer = BeautifulSoup(str(self.bs), features="lxml")
        self.unwrap_items([answer, question])

        question_cloze = question.find("cloze", {"id": cloze["id"]})
        question_cloze.replace_with(self.occluded_question)
        question_clozes = question.findAll("cloze")
        self._occlude_clozes(question_clozes)

        answer_clause = answer.find("cloze", {"id": cloze["id"]})
        answer_clause.replace_with(
            self.answer_template.format(answer_clause.text))

        card_details = {
            "cloze-id": cloze["id"],
            "front": question.text,
            "back": answer.text
        }

        return card_details

    def _occlude_clozes(self, clozes):
        for cloze in clozes:
            cloze.replace_with(self.occluded_gap)

    def unwrap_items(self, items, tags=("html", "body")):
        for item in items:
            self.unwrap_tags(item, tags)

    @staticmethod
    def unwrap_tags(item, tags=("html", "body")):
        for tag in tags:
            item.find(tag).unwrap()


class FormattedClozeOccluder(ClozeOccluder):
    occluded_question = '<span class="highlighted-text">[&hellip;]</span>'
    occluded_gap = '<span class="toned-down-text">[&hellip;]</span>'
    answer_template = '<span class="highlighted-text">[{}]</span>'
