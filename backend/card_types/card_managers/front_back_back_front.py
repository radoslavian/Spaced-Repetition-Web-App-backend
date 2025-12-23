from typing import Dict, List

from django.template import Context, Template

from cards.models import Card, CardImage, Image, Category, CardTemplate
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
        card.front_audio = self.get_sound_from(front)
        card.back_audio = self.get_sound_from(back)
        card.template = self.get_template()
        card.note = self.card_note
        card_categories = self.get_categories()
        card.categories.set(card_categories)
        self._save_front_images(card, front)
        self._save_back_images(card, back)

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

    def _save_metadata(self):
        self.card_note.metadata = {
            "front-back-card-id": self.front_back_card
                                  and self.front_back_card.id.hex,
            "back-front-card-id": self.back_front_card
                                  and self.back_front_card.id.hex
        }

    def get_categories(self) -> List:
        return [Category.objects.get(id__exact=category_id)
                for category_id in
                self.card_note.card_description.get("categories", [])]

    def from_card(self, card):
        required_fields = ["_front", "_back", "template", "categories"]
        self.card_note.card_description = {field: card[field]
                                           for field in required_fields}
        self.front_back_card = card
        card.note = self.card_note
        card.save()
        self._save_metadata()


class DoubleSidedFormatted(FrontBackBackFront):
    default_template_string = "<h3>{{ side.text|safe }}</h3>"

    def _update_text_fields(self, card, back, front):
        template_string = self._get_formatting_template_string()
        card.front = self._render_side(front, template_string)
        card.back = self._render_side(back, template_string)

    def _get_formatting_template_string(self):
        formatting_template_string_db = self._get_db_formatting_template()
        formatting_template_string = self.card_note.card_description.get(
            "formatting_template_string")
        template_string = (formatting_template_string_db
                           or formatting_template_string
                           or self.default_template_string)
        return template_string

    def _get_db_formatting_template(self):
        db_template_title = self.card_note.card_description.get(
            "formatting_template_db")
        template_body = CardTemplate.objects.get(
            title__exact=db_template_title).body if db_template_title else None
        return template_body

    @staticmethod
    def _render_side(side, template_string):
        context_data = {
            "request": {},
            "side": side
        }
        context = Context(context_data)
        template = Template(template_string=template_string)
        return template.render(context)