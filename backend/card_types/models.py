import uuid
from django.db import models
from .card_managers import type_managers
from .card_managers.exceptions import InvalidCardType


class CardNote(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    card_description = models.TextField()
    metadata = models.TextField()
    card_type = models.CharField(max_length=100)

    def save(self, *args, **kwargs):
        self.save_cards()
        super().save(*args, **kwargs)

    @property
    def card_type_instance(self):
        if not self.card_type:
            return None
        cls = type_managers.get(self.card_type)
        if not cls:
            raise InvalidCardType
        return cls(self)

    def save_cards(self):
        """
        Update cards attached to a note.
        Requires invoking .save() of the model if called manually.
        """
        card_type_instance = self.card_type_instance
        if card_type_instance:
            card_type_instance.save_cards()