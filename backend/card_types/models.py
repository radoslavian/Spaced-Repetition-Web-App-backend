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

    @property
    def card_type_instance(self):
        cls = type_managers.get(self.card_type)
        if not cls:
            raise InvalidCardType
        return cls(self)

    def save_cards(self):
        self.card_type_instance.save_cards()