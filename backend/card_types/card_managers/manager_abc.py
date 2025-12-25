from abc import ABC, abstractmethod
from typing import Dict, List

from cards.models import CardTemplate, Sound, Card, CardImage, Image, Category


class CardManager(ABC):
    def __init__(self, card_note):
        self.card_note = card_note

    @abstractmethod
    def save_cards(self):
        pass

    def from_card(self, card):
        self._set_note_description(card)
        self._attach_note_to(card)
        card.save()

    def _attach_note_to(self, card):
        card.note = self.card_note

    def _set_note_description(self, card):
        required_fields = ["_front", "_back", "template", "categories"]
        self.card_note.card_description = card.get_selected_fields(
            required_fields)

    def _get_card_by_id(self, card_id):
        return self.card_note.cards.filter(id=card_id).first()

    def get_template(self):
        template_id = self.card_note.card_description.get("template")
        template_title = self.card_note.card_description.get("template_title")
        get_db_template = CardTemplate.objects.get

        if template_title:
            return get_db_template(title__exact=template_title)
        elif template_id:
            return get_db_template(id__exact=template_id)
        else:
            return None

    def _save_card(self, card: Card, front: Dict, back: Dict):
        # a card must be saved to be present in the database
        # before using any foreign keys
        for update in (self._update_text_fields,
                       self._update_referencing_fields):
            update(card, back, front)
            card.save()
        return card

    @staticmethod
    def _update_text_fields(card, back, front):
        card.front = front.get("text")
        card.back = back.get("text")

    def _update_referencing_fields(self, card, back, front):
        """
        Saves foreign keys to the card.
        """
        self._update_audio_fields(card, back, front)
        card.template = self.get_template()
        card.note = self.card_note
        card_categories = self.get_categories()
        card.categories.set(card_categories)
        self._save_front_images(card, front)
        self._save_back_images(card, back)

    def _update_audio_fields(self, card, back, front):
        card.front_audio = self.get_sound_from(front)
        card.back_audio = self.get_sound_from(back)

    @staticmethod
    def _save_images(card, card_side, side):
        CardImage.objects.filter(card=card, side=side).delete()
        image_ids = card_side.get("images")
        if not image_ids:
            return

        for image_id in image_ids:
            image = Image.objects.get(id__exact=image_id)
            CardImage.objects.create(card=card, image=image, side=side)

    def _save_front_images(self, card, card_side):
        self._save_images(card=card, card_side=card_side, side="front")

    def _save_back_images(self, card, card_side):
        self._save_images(card=card, card_side=card_side, side="back")

    def get_categories(self) -> List:
        return [Category.objects.get(id__exact=category_id)
                for category_id in
                self.card_note.card_description.get("categories", [])]

    @staticmethod
    def _get_formatting_template_string(part: dict):
        """
        Template string for formatting for rendering a card note into card(s).
        """
        db_template_title = part.get("formatting_template_db")
        template_body = CardTemplate.objects.get(
            title__exact=db_template_title).body if db_template_title else None
        return template_body

    @staticmethod
    def get_sound_from(description_fragment: Dict):
        audio_id = description_fragment.get("audio", None)
        return audio_id and Sound.objects.filter(id__exact=audio_id).first()
