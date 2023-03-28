import datetime
import uuid
from datetime import date
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import CheckConstraint, Q, F
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
    def new_review(self, grade):
        return SM2(self.easiness_factor,
                   self.current_real_interval,
                   self.repetitions).review(grade)

    def get_real_interval(self):
        if not self.last_reviewed:
            return 0
        real_interval = (date.today() - self.last_reviewed).days
        return real_interval

    card = models.ForeignKey("Card", on_delete=models.CASCADE,
                             null=False)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE,
                             null=False)
    computed_interval = models.IntegerField(default=0)
    current_real_interval = property(fget=get_real_interval)
    lapses = models.IntegerField(default=0)

    # all_repetitions - cumulative number of repetitions
    # no matter if the review is failed or successful
    # default == 1 - we assume that if the association is created,
    # the user must have seen the card at least
    # once (e.g. during memorization)
    all_repetitions = models.IntegerField(default=1)
    last_reviewed = models.DateField(auto_now=True)
    introduced_on = models.DateField(auto_now_add=True)
    review_date = models.DateField(default=today)
    grade = models.IntegerField(default=4)
    repetitions = models.IntegerField(default=1)
    easiness_factor = models.FloatField(default=2.5)

    class Meta:
        unique_together = ("card", "user",)

    def __str__(self):
        return f"ReviewDataSM2(user='{str(self.user)}' " \
               f"card='{str(self.card)}')"


class Card(models.Model):
    images_number_limit_in_query = 15
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
    images = models.ManyToManyField(
        "Image", through="CardImage")

    class Meta:
        unique_together = ("front", "back",)

    class Decorators:
        def validate_grade(fn):
            def wrapper(self, user, grade: int = 4):
                if 0 > grade or grade > 5 or type(grade) is not int:
                    raise ValueError("Grade should be 0-5 integer.")
                return fn(self, user, grade)

            return wrapper

    @staticmethod
    def _images_getter(side: str):
        if side not in ("front", "back",):
            raise ValueError("The 'side' parameter must be either 'front' "
                             "or 'back'.")

        def getter(self):
            card_images = CardImage.objects.filter(card=self, side=side)\
                .all().order_by('created')[:Card.images_number_limit_in_query]
            images = [card_image.image for card_image in card_images]
            return images
        return getter

    front_images = property(fget=_images_getter("front"))
    back_images = property(fget=_images_getter("back"))

    @staticmethod
    def schedule_date_for_review(user, review_date,
                                 days_range=3) -> datetime.date:
        """Selects date for card review with minimal reviews already assigned
         so that reviews are more evenly distributed.
        """
        dates = [review_date + datetime.timedelta(days=days)
                 for days in range(days_range)]
        dates_reviews = {
            date_review: ReviewDataSM2.objects.filter(
                user=user, review_date=date_review).count()
            for date_review in dates
        }

        return min(dates_reviews, key=dates_reviews.get)

    @Decorators.validate_grade
    def memorize(self, user, grade: int = 4) -> ReviewDataSM2:
        """Generate initial review data for a particular user and (this) card
        and put it into ReviewDataSM2.
        """
        first_review = SM2.first_review(grade)
        optimal_date = self.schedule_date_for_review(
            user, review_date=first_review.review_date, days_range=3)
        review_data = ReviewDataSM2(
            card=self,
            user=user,
            easiness_factor=first_review.easiness,
            computed_interval=first_review.interval,
            repetitions=first_review.repetitions,
            grade=grade,
            review_date=optimal_date)
        try:
            review_data.save()
        except IntegrityError:
            raise CardReviewDataExists

        # for convenience
        return review_data

    @Decorators.validate_grade
    def review(self, user, grade: int = 4):
        """Update ReviewDataSM2 with current review data.
        """
        # 2 - is the highest failed grading
        # 3 - is the lowest successful grading
        review_data = get_object_or_404(ReviewDataSM2, user=user, card=self)
        new_review = review_data.new_review(grade)
        days_range = self._range_of_days(grade, review_data)
        optimal_review_date = self.schedule_date_for_review(
            user=user,
            review_date=new_review.review_date,
            days_range=days_range)

        if grade < 3:
            # updating object's value using F() expression (see below)
            review_data.lapses = F("lapses") + 1
        review_data.all_repetitions = F("all_repetitions") + 1
        review_data.review_date = optimal_review_date
        review_data.grade = grade
        review_data.easiness_factor = new_review.easiness
        review_data.computed_interval = new_review.interval
        review_data.repetitions = new_review.repetitions
        review_data.save()

        # from the documentation:
        # To access the new value (created with the F expression)
        # the object must be reloaded
        # https://docs.djangoproject.com/en/4.1/ref/models/expressions/
        # section about F() expressions
        review_data.refresh_from_db()

        return review_data

    @staticmethod
    def _range_of_days(grade, review_data):
        """Returns range of days within which a review can be assigned.
        """
        # arbitrary thresholds:
        # this if/elif/else has no coverage in tests!
        if review_data.current_real_interval > 30 and grade > 2:
            days_range = 7
        elif 10 < review_data.current_real_interval < 30 and grade > 2:
            days_range = 5
        else:
            days_range = 3
        return days_range

    def forget(self, user):
        ReviewDataSM2.objects.get(card=self, user=user).delete()

    def simulate_reviews(self, user):
        """Simulates reviews for all 0-5 grades. The next review date
        (review_date) is approximate - does not take into account
        daily burden (number of reviews already scheduled for a particular
        day).
        """
        grades = range(6)  # 0-5
        if (review_data := ReviewDataSM2.objects.filter(
                user=user, card=self).first()) is None:
            review_fn = SM2.first_review
        else:
            def review_fn(grade):
                sm = SM2(review_data.easiness_factor,
                         review_data.current_real_interval,
                         review_data.repetitions)
                return sm.review(grade)

        simulation = {}
        for grade in grades:
            data = review_fn(grade)
            simulation[grade] = dict(easiness=data.easiness,
                                     interval=data.interval,
                                     repetitions=data.repetitions,
                                     review_date=data.review_date)
        return simulation

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


class Image(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    image = models.ImageField(upload_to="images/")
    description = models.CharField(max_length=1000)
    cards = models.ManyToManyField("Card", through="CardImage")


class CardImage(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    side = models.CharField(max_length=5,
                            default="front")
    created = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("card", "image", "side",)
        constraints = [
            CheckConstraint(
                check=Q(side__in=("front", "back")),
                name="check_side"
            ),
        ]


# not tested !
class Sound(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    sound = models.FileField(upload_to="sounds/")
    description = models.CharField(max_length=1000)
