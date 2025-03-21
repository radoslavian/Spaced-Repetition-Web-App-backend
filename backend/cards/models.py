import datetime
import hashlib
import uuid
from datetime import date
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import CheckConstraint, Q, F
from treebeard.al_tree import AL_Node
from django.db.utils import IntegrityError
from django.urls import reverse
from .apps import CardsConfig
from .utils.exceptions import CardReviewDataExists, ReviewBeforeDue, \
    CardsDistributionRangeExceeded
from .utils.helpers import today, validate_grade, get_file_hash, make_saver
from .utils.supermemo2 import SM2

encoding = CardsConfig.default_encoding
max_comment_len = CardsConfig.max_comment_len


class CardTemplate(models.Model):
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
    body = models.TextField()

    def __str__(self):
        return f"<{self.title}>"


class CardUserData(models.Model):
    def new_review(self, grade):
        return SM2(self.easiness_factor,
                   self.current_real_interval,
                   self.reviews).review(grade)

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

    # total reviews - cumulative number of repetitions
    # no matter if the review is failed or successful
    # default == 1 - we assume that if the association is created,
    # the user must have seen the card at least
    # once (e.g. during memorization)
    reviews = models.IntegerField(default=1)
    total_reviews = models.IntegerField(default=1)
    last_reviewed = models.DateField(default=today)
    introduced_on = models.DateTimeField(auto_now_add=True)
    review_date = models.DateField(default=today)
    grade = models.IntegerField(default=4)
    easiness_factor = models.FloatField(default=2.5)
    crammed = models.BooleanField(default=False)
    comment = models.TextField(default=None, null=True)

    # for getting memorized cards distribution (in the future) and
    # cards memorization rate (value in days)
    MAX_DISTRIBUTION_RANGE = 31

    def _set_crammed(self, status: bool = False):
        if self.crammed != status:
            self.crammed = status
            self.save()
        return self.crammed

    def add_to_cram(self):
        return self._set_crammed(True)

    def remove_from_cram(self):
        return self._set_crammed(False)

    def _range_of_days(self, grade):
        """Returns range of days within which a review can be assigned.
        """
        # arbitrary thresholds:
        # this if/elif/else has no coverage in tests!
        if self.current_real_interval > 30 and grade > 2:
            days_range = 7
        elif 10 < self.current_real_interval < 30 and grade > 2:
            days_range = 5
        else:
            days_range = 3
        return days_range

    @classmethod
    def get_cards_distribution(cls, user, days_range=3):
        """Returns cards reviews distribution for days in selected
        range.
        """
        # this method is executed in API tests only
        cls.check_distribution_days_range(days_range)
        selected_categories = user.get_user_categories_trees()
        dates = [date.today() + datetime.timedelta(days=days)
                 for days in range(1, days_range + 1)]

        return {
            str(review_date): cls.objects.filter(
                user=user,
                review_date=review_date,
                card__categories__in=selected_categories
            ).distinct().count()
            for review_date in dates
        }

    @classmethod
    def get_cards_memorization_distribution(cls, user, days_range=3):
        # this method is executed in API tests only
        cls.check_distribution_days_range(days_range)
        selected_categories = user.get_user_categories_trees()
        dates = [date.today() - datetime.timedelta(days=days)
                 for days in range(days_range)]

        return {
            str(introduction_date): cls.objects.filter(
                user=user,
                introduced_on__day=introduction_date.day,
                introduced_on__month=introduction_date.month,
                introduced_on__year=introduction_date.year,
                card__categories__in=selected_categories
            ).distinct().count()
            for introduction_date in dates
        }

    @classmethod
    def check_distribution_days_range(cls, days_range):
        if days_range > cls.MAX_DISTRIBUTION_RANGE:
            raise CardsDistributionRangeExceeded(
                f"Allowed days range is set to {cls.MAX_DISTRIBUTION_RANGE} "
                "days.")

    @classmethod
    def get_efactor_distribution(cls, user):
        user_memorized_cards = cls.objects.filter(user=user)
        e_factors = {
            card.easiness_factor: str(round(card.easiness_factor, 2))
            for card in user_memorized_cards
        }

        e_factors_distribution = [{
            "e-factor": e_factors[e_factor],
            "count": user_memorized_cards.filter(
                easiness_factor=e_factor).count()
        } for e_factor in sorted(e_factors.keys())]

        return e_factors_distribution

    @classmethod
    def get_grades_distribution(cls, user):
        user_memorized_cards = cls.objects.filter(user=user)
        grades = range(0, 6)  # grades are 0 to (including) 5

        return {
            str(grade): user_memorized_cards.filter(grade=grade).count()
            for grade in grades
        }

    def schedule_date_for_review(self, review_date,
                                 days_range=3) -> datetime.date:
        """Selects date for card review with minimal reviews already assigned
         so that reviews are more evenly distributed.
        """
        dates = [review_date + datetime.timedelta(days=days)
                 for days in range(days_range)]
        dates_reviews = {
            date_review: CardUserData.objects.filter(
                user=self.user, review_date=date_review).count()
            for date_review in dates
        }

        return min(dates_reviews, key=dates_reviews.get)

    def review(self, grade):
        """Update record with current review data.
        """
        validate_grade(grade)
        if self.review_date > datetime.datetime.today().date():
            raise ReviewBeforeDue
        new_review = self.new_review(grade)
        days_range = self._range_of_days(grade)
        optimal_review_date = self.schedule_date_for_review(
            review_date=new_review.review_date,
            days_range=days_range)

        if grade < 4:
            self.add_to_cram()

        if grade < 3:
            # updating object's value using F() expression (see below)
            self.lapses = F("lapses") + 1

        self.total_reviews = F("total_reviews") + 1
        self.review_date = optimal_review_date
        self.grade = grade
        self.easiness_factor = new_review.easiness
        self.computed_interval = new_review.interval
        self.reviews = new_review.repetitions
        self.last_reviewed = datetime.datetime.now().date()
        self.save()

        # from the documentation:
        # To access the new value (created with the F expression)
        # the object must be reloaded
        # https://docs.djangoproject.com/en/4.1/ref/models/expressions/
        # section about F() expressions
        self.refresh_from_db()

    def get_absolute_url(self):
        return reverse("memorized_card",
                       kwargs={"pk": self.card.id,
                               "user_id": self.user.id})

    class Meta:
        unique_together = ("card", "user",)

    @staticmethod
    def keys():
        return ['computed_interval', 'lapses', 'reviews', 'total_reviews',
                'last_reviewed', 'introduced_on', 'review_date', 'grade',
                'easiness_factor', 'crammed', 'comment']

    def values(self):
        return [self.computed_interval, self.lapses, self.reviews,
                self.total_reviews, self.last_reviewed, self.introduced_on,
                self.review_date, self.grade, self.easiness_factor,
                self.crammed, self.comment]

    def __getitem__(self, key):
        return dict(zip(self.keys(), self.values()))[key]

    def __repr__(self):
        return f"CardUserData(user='{str(self.user)}' " \
               f"card='{str(self.card)}')"

    def __str__(self):
        return "\n".join(f"{key}: {self[key]}" for key in self.keys())


class Card(models.Model):
    images_number_limit_in_query = 15
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    # auto_now - automatically sets the field to "now" each time
    # the object is saved
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    front = models.TextField()
    back = models.TextField()
    template = models.ForeignKey(CardTemplate, on_delete=models.PROTECT,
                                 null=True,
                                 blank=True,
                                 related_name="cards")
    categories = models.ManyToManyField("cards.Category",
                                        related_name="cards")
    images = models.ManyToManyField(
        "Image", through="CardImage")
    front_audio = models.ForeignKey("Sound", on_delete=models.SET_NULL,
                                    null=True,
                                    blank=True,
                                    related_name="cards_front")
    back_audio = models.ForeignKey("Sound", on_delete=models.SET_NULL,
                                   null=True,
                                   blank=True,
                                   related_name="cards_back")

    class Meta:
        unique_together = ("front", "back",)

    @staticmethod
    def _make_images_getter(side: str):
        """Returns function for getting front or back images from
        the properties.
        """
        if side not in ("front", "back",):
            raise ValueError("The 'side' parameter must be either 'front' "
                             "or 'back'.")

        def getter(self):
            card_images = CardImage.objects.filter(card=self, side=side) \
                              .all().order_by('created')[
                          :Card.images_number_limit_in_query]
            images = [card_image.image for card_image in card_images]
            return images

        return getter

    front_images = property(fget=_make_images_getter("front"))
    back_images = property(fget=_make_images_getter("back"))

    def memorize(self, user, grade: int = 4) -> CardUserData:
        """Generate initial review data for a particular user and (this) card
        and put it into CardUserData.
        """
        if grade < 4:
            crammed = True
        else:
            crammed = False
        validate_grade(grade)
        first_review = SM2.first_review(grade)
        review_data = CardUserData(
            card=self,
            user=user,
            easiness_factor=first_review.easiness,
            computed_interval=first_review.interval,
            reviews=first_review.repetitions,
            crammed=crammed,
            grade=grade)
        optimal_date = review_data.schedule_date_for_review(
            review_date=first_review.review_date, days_range=3)
        review_data.review_date = optimal_date

        try:
            review_data.save()
        except IntegrityError:
            raise CardReviewDataExists

        # for convenience
        return review_data

    def review(self, user, grade: int = 4):
        """Shorthand for making a review.
        """
        review_data = CardUserData.objects.get(user=user, card=self)
        review_data.review(grade=grade)
        return review_data

    def forget(self, user):
        CardUserData.objects.get(card=self, user=user).delete()

    def simulate_reviews(self, user=None):
        """Simulates reviews for all 0-5 grades. The next review date
        (review_date) is approximate - does not take into account
        daily burden (number of reviews already scheduled for a particular
        day).
        """
        grades = range(6)  # 0-5
        if not user or (review_data := CardUserData.objects.filter(
                user=user, card=self).first()) is None:
            review_fn = SM2.first_review
        else:
            def review_fn(grade):
                sm = SM2(review_data.easiness_factor,
                         review_data.current_real_interval,
                         review_data.reviews)
                return sm.review(grade)

        simulation = {}
        for grade in grades:
            data = review_fn(grade)
            simulation[grade] = dict(easiness=data.easiness,
                                     interval=data.interval,
                                     reviews=data.repetitions,
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
        null=True,
        blank=True
    )
    node_order_by = ["name"]

    class Meta:
        unique_together = ("name", "parent")

    def __str__(self):
        return f"<{self.name}>"


def get_random_sha1():
    return hashlib.sha1(
        bytes(str(uuid.uuid4()), "utf-8")).hexdigest()

class Image(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    image = models.ImageField(upload_to="images/",
                              null=False)
    sha1_digest = models.CharField(
        max_length=40,
        unique=True,
        null=False,
        default=get_random_sha1)
    description = models.CharField(max_length=1000)
    cards = models.ManyToManyField("Card", through="CardImage")

    def save(self, *args, **kwargs):
        _save = make_saver(Image, "image", "sha1_digest")
        _save(self, *args, **kwargs)

    def __str__(self):
        return str(self.image)


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


class Sound(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    sound_file = models.FileField(upload_to="sounds/", null=False)
    description = models.CharField(max_length=1000)
    sha1_digest = models.CharField(
        max_length=40,
        unique=True,
        null=False,
        default=get_random_sha1)

    def save(self, *args, **kwargs):
        _save = make_saver(Sound, "sound_file", "sha1_digest")
        _save(self, *args, **kwargs)

    def __str__(self):
        return str(self.sound_file)
