from typing import Sequence
from uuid import UUID

from cards.management.fr_importer.items_parser.modules.html_formatted_card import \
    HtmlFormattedCard
from cards.management.fr_importer.items_parser.modules.html_memorized_card import \
    HtmlFormattedMemorizedCard
from cards.models import Card, CardTemplate, Category


class ImportedCard:
    def __init__(self, card_object: HtmlFormattedCard
                                    | HtmlFormattedMemorizedCard):
        self._card = Card(front=card_object.question_output_text,
                          back=card_object.answer_output_text)

    def save(self):
        self._card.save()

    def set_template_by_uuid(self, template_id: UUID|str):
        template = CardTemplate.objects.get(id=template_id)
        self.set_template(template)

    def set_template_by_title(self, exact_template_title: str):
        template = CardTemplate.objects.get(title__exact=exact_template_title)
        self.set_template(template)

    def set_template(self, template: CardTemplate):
        self._card.template = template

    def set_categories(self, categories: Sequence[Category|UUID|str]):
        _categories = [self._match_category(_category)
                       for _category in categories]
        self._card.categories.set(_categories)

    @staticmethod
    def _match_category(_category: Category | UUID | str):
        match _category:
            case UUID() | str():
                return Category.objects.get(id=_category)
            case Category():
                return _category
            case _:
                raise ValueError("Invalid argument for setting categories.")

