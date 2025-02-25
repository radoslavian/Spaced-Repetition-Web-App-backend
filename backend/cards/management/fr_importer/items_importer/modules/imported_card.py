from uuid import UUID

from cards.management.fr_importer.items_parser.modules.html_formatted_card import \
    HtmlFormattedCard
from cards.management.fr_importer.items_parser.modules.html_memorized_card import \
    HtmlFormattedMemorizedCard
from cards.models import Card, CardTemplate


class ImportedCard:
    def __init__(self, card_object: HtmlFormattedCard
                                    | HtmlFormattedMemorizedCard):
        self.card = Card(front=card_object.question_output_text,
                         back=card_object.answer_output_text)

    def save(self):
        self.card.save()

    def set_template_by_uuid(self, template_id: UUID|str):
        template = CardTemplate.objects.get(id=template_id)
        self.set_template(template)

    def set_template(self, template: CardTemplate):
        self.card.template = template
        self.card.save()
