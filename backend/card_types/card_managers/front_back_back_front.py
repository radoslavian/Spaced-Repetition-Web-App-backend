import json
from typing import Dict

from cards.models import Card
from .manager_abc import CardManager


class FrontBackBackFront(CardManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.front_back_card = self._get_card_by_id(
            self.note_metadata.get("front-back-card-id"))
        self.back_front_card = self._get_card_by_id(
            self.note_metadata.get("back-front-card-id"))

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
        card.front_audio = self.get_sound_from(front)
        card.back_audio = self.get_sound_from(back)
        card.template = self.get_template()
        card.note = self.card_note
        card.save()
        return card

    def _save_metadata(self):
        if not all([self.front_back_card, self.back_front_card]):
            return
        metadata = {
            "front-back-card-id": self.front_back_card.id.hex,
            "back-front-card-id": self.back_front_card.id.hex
        }
        self.card_note.metadata = json.dumps(metadata)