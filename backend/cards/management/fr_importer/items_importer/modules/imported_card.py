from cards.management.fr_importer.items_parser.modules.html_formatted_card import \
    HtmlFormattedCard
from cards.management.fr_importer.items_parser.modules.html_memorized_card import \
    HtmlFormattedMemorizedCard
from cards.models import Card


class ImportedCard:
    def __init__(self, card_object: HtmlFormattedCard
                                    | HtmlFormattedMemorizedCard):
        self.card = Card(front=card_object.question_output_text,
                         back=card_object.answer_output_text)

    def save(self):
        self.card.save()
