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

    def _get_crammed_cards(self):
        return CardUserData.objects.filter(user=self, crammed=True)\
            .order_by("introduced_on")

    crammed_cards = property(fget=_get_crammed_cards)
    memorized_cards = models.ManyToManyField(
        "cards.Card",
        through="cards.CardUserData",
        related_name="reviewing_users")
    selected_categories = models.ManyToManyField(
        "cards.Category",
        related_name="category_users")
    ignored_cards = models.ManyToManyField(
        "cards.Card",
        related_name="ignoring_users")

    @property
    def selected_categories_ids(self):
        return [str(category.id) for category in
                self.selected_categories.all()]

    def get_user_categories_trees(self):
        """Returns user categories together with categories included
        in trees.
        """
        user_categories = []
        for selected_category in self.selected_categories.all():
            user_categories.extend(Category.get_tree(
                selected_category))
        return user_categories


from cards.models import CardUserData, Category
