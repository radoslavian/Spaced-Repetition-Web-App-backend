import uuid
from django.db import models


class CardNote(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    card_description = models.TextField()
    metadata = models.TextField()
    card_type = models.CharField(max_length=100)