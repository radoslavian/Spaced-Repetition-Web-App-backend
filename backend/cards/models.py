import uuid
from datetime import date

from django.contrib.auth import get_user_model
from django.db import models
from rest_framework.generics import get_object_or_404
from treebeard.al_tree import AL_Node
from django.db.utils import IntegrityError
from .apps import CardsConfig
from .utils.exceptions import CardReviewDataExists
from .utils.helpers import today
from .utils.supermemo2 import SM2

encoding = CardsConfig.default_encoding
max_comment_len = CardsConfig.max_comment_len


class Template(models.Model):
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


class ReviewDataSM2(models.Model):
    def get_real_interval(self):
        if not self.last_reviewed:
            return 0
        real_interval = (date.today() - self.last_reviewed).days
        return real_interval

    card = models.ForeignKey("Card", on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    current_real_interval = property(fget=get_real_interval)
    last_reviewed = models.DateField(auto_now=True)
    introduced_on = models.DateField(auto_now_add=True)
    review_date = models.DateField(default=today)
    computed_interval = models.IntegerField(default=0)
    grade = models.IntegerField(default=4)
    repetitions = models.IntegerField(default=1)
    easiness_factor = models.FloatField(default=2.5)

    class Meta:
        unique_together = ("card", "user",)

    def __str__(self):
        return f"ReviewDataSM2(user='{str(self.user)}' " \
               f"card='{str(self.card)}')"


class Card(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    # auto_now - automatically sets the field to now each time
    # the object is saved
    last_modified = models.DateTimeField(auto_now=True)
    front = models.TextField()
    back = models.TextField()
    template = models.ForeignKey(Template, on_delete=models.PROTECT,
                                 null=True, related_name="cards")
    commenting_users = models.ManyToManyField(
        get_user_model(), through="CardComment")

    class Meta:
        unique_together = ("front", "back",)

    def memorize(self, user: get_user_model(), grade=4) -> ReviewDataSM2:
        """Generate initial review data for a particular user and (this) card
        and put it into ReviewDataSM2.
        """
        first_review = SM2.first_review(grade)
        review_data = ReviewDataSM2(
            card=self,
            user=user,
            easiness_factor=first_review.easiness,
            computed_interval=first_review.interval,
            repetitions=first_review.repetitions,
            grade=grade,
            review_date=first_review.review_date)
        try:
            review_data.save()
        except IntegrityError:
            raise CardReviewDataExists

        # for convenience
        return review_data

    def review(self, user, grade=4):
        """Update ReviewDataSM2 with current review data.
        """
        review_data = get_object_or_404(ReviewDataSM2, user=user, card=self)
        new_review = SM2(review_data.easiness_factor,
                         review_data.current_real_interval,
                         review_data.repetitions).review(grade)

        review_data.review_date = new_review.review_date
        review_data.grade = grade
        review_data.easiness_factor = new_review.easiness
        review_data.computed_interval = new_review.interval
        review_data.repetitions = new_review.repetitions
        review_data.save()

        return review_data

    def forget(self, user):
        ReviewDataSM2.objects.get(card=self, user=user).delete()

    def __str__(self):
        MAX_LEN = (25, 25,)  # for question and answer
        question = (self.front[:MAX_LEN[0]] + " ..."
                    if len(self.front) > MAX_LEN[0]
                    else self.front)
        answer = (self.back[:MAX_LEN[0]] + " ..."
                  if len(self.back) > MAX_LEN[1]
                  else self.back)
        serialized = f"Card(Q: {question}; A: {answer})"

        return serialized


class CardComment(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    text = models.CharField(max_length=max_comment_len)

    class Meta:
        unique_together = ("card", "user")


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
