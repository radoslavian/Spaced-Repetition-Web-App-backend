from abc import ABC, abstractmethod
from typing import Dict

from cards.models import CardTemplate, Sound


class CardManager(ABC):
    def __init__(self, card_note):
        self.card_note = card_note

    @abstractmethod
    def save_cards(self):
        pass

    @abstractmethod
    def from_card(self, card):
        pass

    def _get_card_by_id(self, card_id):
        return self.card_note.cards.filter(id=card_id).first()

    def get_template(self):
        return CardTemplate.objects.filter(
            id__exact=self.card_note.card_description.get("template")).first()

    @staticmethod
    def get_sound_from(description_fragment: Dict):
        audio_id = description_fragment.get("audio", None)
        return audio_id and Sound.objects.filter(id__exact=audio_id).first()
