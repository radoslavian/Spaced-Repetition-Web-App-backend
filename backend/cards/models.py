import uuid

from django.contrib.auth import get_user_model
from django.db import models
from treebeard.al_tree import AL_Node

from .apps import CardsConfig
from .utils.model_mixins import TriggeredLastModifiedUpdateMixin

encoding = CardsConfig.default_encoding
max_comment_len = CardsConfig.max_comment_len


class Template(models.Model, TriggeredLastModifiedUpdateMixin):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    class Meta:
        unique_together = ("title", "description", "body",)

    last_modified = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=100)
    description = models.TextField()

    # body will eventually contain template for rendering
    # with fields for question and answer
    body = models.TextField()

    def __str__(self):
        return f"<{self.title}>"


class Card(models.Model, TriggeredLastModifiedUpdateMixin):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    last_modified = models.DateTimeField(auto_now=True)
    front = models.TextField()
    back = models.TextField()
    template = models.ForeignKey(Template, on_delete=models.PROTECT,
                                 null=True, related_name="cards")
    commenting_users = models.ManyToManyField(
        get_user_model(), through="CardComment")

    class Meta:
        unique_together = ("front", "back",)

    def __str__(self):
        MAX_LEN = 50
        serialized = f"Q: {self.front}; A: {self.back}"
        if len(serialized) > MAX_LEN:
            serialized = serialized[:MAX_LEN] + " ..."

        return serialized


class CardComment(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    text = models.CharField(max_length=max_comment_len)

    class Meta:
        unique_together = ("card", "user")


class RepetitionDataSM2(models.Model):
    # start here
    pass


class Category(AL_Node):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(max_length=64)
    parent = models.ForeignKey(
        "self",
        related_name="sub_categories",
        on_delete=models.PROTECT,
        db_index=True,
        null=True
    )
    node_order_by = ["name"]

    class Meta:
        unique_together = ("name", "parent")

    def __str__(self):
        return f"<{self.name}>"

