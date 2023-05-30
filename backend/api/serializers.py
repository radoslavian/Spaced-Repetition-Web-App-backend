from django.urls import reverse
from rest_framework import serializers
from rest_framework_recursive.fields import RecursiveField
from cards.models import Card, Image, CardImage, CardUserData, Category


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ("id", "image",)


class CategoryForCardSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="name")
    key = serializers.CharField(source="id")

    class Meta:
        model = Category
        fields = ("key", "title",)


class CategorySerializer(CategoryForCardSerializer):
    children = RecursiveField(many=True, source="sub_categories")

    class Meta:
        model = Category
        fields = ("key", "title", "children",)


class CardForEditingSerializer(serializers.ModelSerializer):
    front_images = ImageSerializer(many=True)
    back_images = ImageSerializer(many=True)
    categories = CategoryForCardSerializer(many=True)

    class Meta:
        model = Card
        fields = ("id", "front", "back", "template", "last_modified",
                  "front_images", "back_images", "categories",)
        read_only_fields = ("id", "last_modified", "front_images",
                            "back_images", "categories")


class CardReviewDataSerializer(serializers.ModelSerializer):
    body = serializers.SerializerMethodField()
    projected_review_data = serializers.SerializerMethodField()
    categories = CategoryForCardSerializer(source="card.categories",
                                           many=True)
    cram_link = serializers.SerializerMethodField()
    created_on = serializers.CharField(source="card.created_on")
    id = serializers.CharField(source="card.id")

    @staticmethod
    def get_cram_link(obj):
        """Returns cram_link whose non-null value signifies the card is
        cram-queued and which in turn may be used for removing card from cram.
        """
        if not obj.crammed:
            return None
        return reverse("cram_single_card",
                       kwargs={"card_pk": obj.card.id,
                               "user_id": obj.user.id})

    @staticmethod
    def get_projected_review_data(obj):
        """Returns reviews simulation for currently scheduled cards only.
        """
        if obj.current_real_interval > 0:
            return obj.card.simulate_reviews(user=obj.user)

    @staticmethod
    def get_body(obj):
        return obj.card.body

    class Meta:
        model = CardUserData
        exclude = ("user", "crammed", "card")
        read_only_fields = ("body", "computed_interval", "lapses",
                            "total_reviews", "last_reviewed", "introduced_on",
                            "review_date", "grade", "reviews",
                            "easiness_factor", "card", "cram_link", "id")


class CardUserNoReviewDataSerializer(serializers.ModelSerializer):
    categories = CategoryForCardSerializer(many=True)

    class Meta:
        model = Card
        fields = ("id", "body", "categories", "created_on")
        read_only_fields = ("id", "body", "categories",)
