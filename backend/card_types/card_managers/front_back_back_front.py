from cards.models import Card
from .manager_abc import CardManager


class FrontBackBackFront(CardManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.front_back_card = self._get_card_by_id(
            self.card_note.metadata.get("front-back-card-id"))
        self.back_front_card = self._get_card_by_id(
            self.card_note.metadata.get("back-front-card-id"))

    def save_cards(self):
        front = self.card_note.card_description.get("_front", {})
        back = self.card_note.card_description.get("_back", {})

        front_back_card = self.front_back_card or Card()
        self.front_back_card = self._save_card(card=front_back_card,
                                               front=front,
                                               back=back)

        back_front_card = self.back_front_card or Card()
        self.back_front_card = self._save_card(card=back_front_card,
                                               front=back,
                                               back=front)
        self._save_metadata()

    def _save_metadata(self):
        self.card_note.metadata = {
            "front-back-card-id": self.front_back_card
                                  and self.front_back_card.id.hex,
            "back-front-card-id": self.back_front_card
                                  and self.back_front_card.id.hex
        }

    def from_card(self, card):
        super().from_card(card)
        self._save_metadata()

    def _attach_note_to(self, card):
        super()._attach_note_to(card)
        self.front_back_card = card