from django.template import Template, Context

from card_types.card_managers.manager_abc import CardManager
from cards.models import Card


class SingleSidedFormatted(CardManager):
    def save_cards(self):
        front = self.card_note.card_description.get("_front", {})
        back = self.card_note.card_description.get("_back", {})
        card = self.card_note.cards.first() or Card()
        self._save_card(card=card, front=front, back=back)

    def _update_text_fields(self, card, back, front):
        card.front = self._render_side(front)
        card.back = self._render_side(back)

    def _render_side(self, side):
        context_data = {
            "side": side
        }
        side_template_string = self._get_formatting_template_string(side)
        context = Context(context_data)
        template = Template(template_string=side_template_string)
        return template.render(context)

    def _set_note_description(self, card):
        required_fields = ["_front", "_back", "template", "categories"]
        selected_fields = card.get_selected_fields(required_fields)
        selected_fields["_front"]["card_question_definition"] = \
            selected_fields["_front"].pop("text")
        selected_fields["_back"]["answer"] = \
            selected_fields["_back"].pop("text")

        self.card_note.card_description = selected_fields