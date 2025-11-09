import json
from typing import Dict

from cards.models import Card, CardTemplate
from .manager_abc import CardManager


class FrontBackBackFront(CardManager):
    def __init__(self, card_note):
        self.card_note = card_note
        self.front_back_card = self._get_card_by_id(
            self.note_metadata.get("front-back-card-id"))
        self.back_front_card = self._get_card_by_id(
            self.note_metadata.get("back-front-card-id"))

    @property
    def note_metadata(self) -> Dict:
        if self.card_note.metadata:
            return json.loads(self.card_note.metadata)
        return {}

    def _get_card_by_id(self, card_id):
        return self.card_note.cards.filter(id=card_id).first()

    def save_cards(self):
        front = self.card_description.get("front", {})
        back = self.card_description.get("back", {})

        front_back_card = self.front_back_card or Card()
        self.front_back_card = self._save_card(card=front_back_card,
                                               front=front,
                                               back=back)

        back_front_card = self.back_front_card or Card()
        self.back_front_card = self._save_card(card=back_front_card,
                                               front=back,
                                               back=front)

        self._save_metadata()

    def _save_card(self, card: Card, front: Dict, back: Dict):
        card.front = front.get("text")
        card.back = back.get("text")
        card.note = self.card_note
        card.template = self.get_template()
        card.save()
        return card

    def get_template(self):
        return CardTemplate.objects.filter(
            id__exact=self.card_description.get("template")).first()

    @property
    def card_description(self):
        return (self.card_note.card_description and
                json.loads(self.card_note.card_description))

    def _save_metadata(self):
        if not all([self.front_back_card, self.back_front_card]):
            return
        metadata = {
            "front-back-card-id": self.front_back_card.id.hex,
            "back-front-card-id": self.back_front_card.id.hex
        }
        self.card_note.metadata = json.dumps(metadata)
