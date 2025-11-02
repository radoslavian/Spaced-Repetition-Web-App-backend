import json
from cards.models import Card
from .manager_abc import CardManager


class FrontBackBackFront(CardManager):
    def __init__(self, card_note):
        self.back_front_card = None
        self.front_back_card = None
        self.card_note = card_note

    def save_cards(self):
        data = json.loads(self.card_note.card_description)
        self.front_back_card = Card.objects.create(front=data["front"]["text"],
                                                   back=data["back"]["text"],
                                                   note=self.card_note)
        self.back_front_card = Card.objects.create(front=data["back"]["text"],
                                                   back=data["front"]["text"],
                                                   note=self.card_note)

        self._save_metadata()

    def _save_metadata(self):
        if not all([self.front_back_card, self.back_front_card]):
            return
        metadata = {
            "front-back-card-id": self.front_back_card.id.hex,
            "back-front-card-id": self.back_front_card.id.hex
        }
        self.card_note.metadata = json.dumps(metadata)