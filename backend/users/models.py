import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.

class User(AbstractUser):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    # selected_categories, rel_name=category_users
    selected_categories = models.ManyToManyField(
        "cards.Category",
        related_name="category_users")
    ignored_cards = models.ManyToManyField(
        "cards.Card",
        related_name="ignoring_users")
    cram_queue = models.ManyToManyField(
        "cards.Card",
        related_name="cramming_users")
    commented_cards = models.ManyToManyField(
        "cards.Card",
        through="cards.CardComment")
    cards_review_data = models.ManyToManyField(
        "cards.Card",
        through="cards.ReviewDataSM2",
        related_name="reviewing_users")
