from django.urls import reverse
from rest_framework.serializers import CharField, ModelSerializer, \
    SerializerMethodField, DateTimeField
from rest_framework_recursive.fields import RecursiveField
from api.utils.helpers import get_card_body
from cards.models import Card, Image, CardUserData, Category


class ImageSerializer(ModelSerializer):
    class Meta:
        model = Image
        fields = ("id", "image",)


class CategoryForCardSerializer(ModelSerializer):
    title = CharField(source="name")
    key = CharField(source="id")

    class Meta:
        model = Category
        fields = ("key", "title",)


class CategorySerializer(CategoryForCardSerializer):
    children = RecursiveField(many=True, source="sub_categories")

    class Meta:
        model = Category
        fields = ("key", "title", "children",)


class CardForEditingSerializer(ModelSerializer):
    front_images = ImageSerializer(many=True)
    back_images = ImageSerializer(many=True)
    categories = CategoryForCardSerializer(many=True)

    class Meta:
        model = Card
        fields = ("id", "front", "back", "template", "last_modified",
                  "front_images", "back_images", "categories",)
        read_only_fields = ("id", "last_modified", "front_images",
                            "back_images", "categories")


class CrammedCardReviewDataSerializer(ModelSerializer):
    body = SerializerMethodField()
    categories = CategoryForCardSerializer(source="card.categories",
                                           many=True)
    cram_link = SerializerMethodField()
    created_on = DateTimeField(source="card.created_on")
    front_audio = SerializerMethodField()
    back_audio = SerializerMethodField()
    id = CharField(source="card.id")

    @staticmethod
    def get_front_audio(obj):
        if obj.question.front_audio:
            return obj.question.front_audio.sound_file.url

    @staticmethod
    def get_back_audio(obj):
        if obj.question.back_audio:
            return obj.question.back_audio.sound_file.url

    def get_body(self, obj):
        request = self.context.get("request")
        return get_card_body(obj.question, request)

    @staticmethod
    def get_cram_link(obj):
        """Returns cram_link whose non-null value signifies the card is
        cram-queued and which in turn may be used for removing card from cram.
        """
        return reverse("cram_single_card",
                       kwargs={"card_pk": obj.question.id,
                               "user_id": obj.user.id})

    class Meta:
        model = CardUserData
        exclude = ("user", "crammed", "card",)
        read_only_fields = ("body", "computed_interval", "lapses",
                            "total_reviews", "last_reviewed", "introduced_on",
                            "review_date", "grade", "reviews",
                            "easiness_factor", "card", "cram_link", "id",)


class CardReviewDataSerializer(CrammedCardReviewDataSerializer):
    projected_review_data = SerializerMethodField()

    @staticmethod
    def get_projected_review_data(obj):
        """Returns reviews simulation for currently scheduled cards only.
        """
        if obj.current_real_interval > 0:
            return obj.question.simulate_reviews(user=obj.user)

    def get_cram_link(self, obj):
        if not obj.crammed:
            return None
        return super().get_cram_link(obj)


class CardUserNoReviewDataSerializer(ModelSerializer):
    categories = CategoryForCardSerializer(many=True)
    front_audio = SerializerMethodField()
    back_audio = SerializerMethodField()
    body = SerializerMethodField()

    def get_body(self, obj):
        request = self.context.get("request")
        return get_card_body(obj, request)

    @staticmethod
    def get_front_audio(obj):
        if obj.front_audio:
            return obj.front_audio.sound_file.url

    @staticmethod
    def get_back_audio(obj):
        if obj.back_audio:
            return obj.back_audio.sound_file.url

    class Meta:
        model = Card
        fields = ("id", "body", "categories", "created_on", "front_audio",
                  "back_audio")
        read_only_fields = ("id", "body", "categories", "created_on",
                            "front_audio", "back_audio")


class AllCardsSerializer(CardUserNoReviewDataSerializer):
    computed_interval = SerializerMethodField()
    type = SerializerMethodField()
    lapses = SerializerMethodField()
    total_reviews = SerializerMethodField()
    last_reviewed = SerializerMethodField()
    introduced_on = SerializerMethodField()
    review_date = SerializerMethodField()
    grade = SerializerMethodField()
    reviews = SerializerMethodField()
    easiness_factor = SerializerMethodField()
    cram_link = SerializerMethodField()

    def get_cram_link(self, card: Card):
        card_user_data = self.get_card_user_data(card)
        if not card_user_data or not card_user_data.crammed:
            return None
        return reverse("cram_single_card",
                       kwargs={"card_pk": card.id,
                               "user_id": card_user_data.user.id})

    def get_easiness_factor(self, card: Card):
        return self.get_card_field(card, "easiness_factor")

    def get_reviews(self, card: Card):
        return self.get_card_field(card, "reviews")

    def get_grade(self, card: Card):
        return self.get_card_field(card, "grade")

    def get_review_date(self, card: Card):
        return self.get_card_field(card, "review_date")

    def get_introduced_on(self, card: Card):
        return self.get_card_field(card, "introduced_on")

    def get_last_reviewed(self, card: Card):
        return self.get_card_field(card, "last_reviewed")

    def get_total_reviews(self, card: Card):
        return self.get_card_field(card, "total_reviews")

    def get_lapses(self, card: Card):
        return self.get_card_field(card, "lapses")

    def get_type(self, card: Card):
        card_user_data = self.get_card_user_data(card)
        if card_user_data:
            return "memorized"
        return "queued"

    def get_computed_interval(self, card: Card):
        return self.get_card_field(card, "computed_interval")

    def get_card_user_data(self, card):
        user = self.get_user()
        self.card_user_data = CardUserData.objects.filter(
            card=card, user=user).first()
        return self.card_user_data

    def get_user(self):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        return user

    def get_card_field(self, card: Card, field: str):
        card_user_data = self.get_card_user_data(card)
        return getattr(card_user_data, field, None)

    class Meta:
        model = Card
        fields = ("id", "body", "categories", "created_on", "front_audio",
                  "back_audio", "computed_interval", "type", "lapses",
                  "total_reviews", "last_reviewed", "introduced_on",
                  "review_date", "grade", "reviews", "easiness_factor",
                  "cram_link",)
        read_only_fields = ("id", "body", "categories", "created_on",
                            "front_audio", "back_audio",
                            "computed_interval", "type", "lapses",
                            "total_reviews", "last_reviewed", "introduced_on",
                            "review_date", "grade", "reviews",
                            "easiness_factor", "cram_link",)
