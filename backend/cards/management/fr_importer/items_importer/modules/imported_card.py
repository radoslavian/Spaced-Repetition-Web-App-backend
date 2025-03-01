from typing import Sequence
from uuid import UUID

from cards.management.fr_importer.items_importer.modules.file_appenders import \
    add_image_get_instance
from cards.management.fr_importer.items_parser.modules.html_formatted_card import \
    HtmlFormattedCard
from cards.management.fr_importer.items_parser.modules.html_memorized_card import \
    HtmlFormattedMemorizedCard
from cards.models import Card, CardTemplate, Category, CardImage


class ImportedCard:
    def __init__(self, card_object: HtmlFormattedCard
                                    | HtmlFormattedMemorizedCard):
        self._card = self.create_card(card_object)
        self._add_images(card_object)

    @staticmethod
    def create_card(card_object):
        card = Card(front=card_object.question_output_text,
                    back=card_object.answer_output_text)
        card.save()
        return card

    def _add_images(self, card_object):
        front_image_path = card_object["question"]["image_file_path"]
        back_image_path = card_object["answer"]["image_file_path"]
        if front_image_path:
            self._add_image(front_image_path, "front")
        if back_image_path:
            self._add_image(back_image_path, "back")

    def _add_image(self, image_path, side):
        image_instance = add_image_get_instance(image_path)
        card_image = CardImage(card=self._card,
                               image=image_instance,
                               side=side)
        card_image.save()

    def save(self):
        self._card.save()

    def set_template_by_uuid(self, template_id: UUID | str):
        template = CardTemplate.objects.get(id=template_id)
        self.set_template(template)

    def set_template_by_title(self, exact_template_title: str):
        template = CardTemplate.objects.get(title__exact=exact_template_title)
        self.set_template(template)

    def set_categories(self, categories: Sequence[Category | UUID | str]):
        _categories = [self._match_category(_category)
                       for _category in categories]
        self._card.categories.set(_categories)

    def set_template(self, template: CardTemplate):
        self._card.template = template

    @property
    def card_instance(self):
        return self._card

    @staticmethod
    def _match_category(_category: Category | UUID | str):
        match _category:
            case UUID() | str():
                return Category.objects.get(id=_category)
            case Category():
                return _category
            case _:
                raise ValueError("Invalid argument for setting categories.")
