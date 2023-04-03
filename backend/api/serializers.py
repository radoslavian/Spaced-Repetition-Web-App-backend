from rest_framework import serializers
from cards.models import Card, Image, CardImage, ReviewDataSM2, Category


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ("id", "image",)


class CategoryForCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name",)


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

    @staticmethod
    def get_body(obj):
        return obj.card.body

    @staticmethod
    def get_projected_review_data(obj):
        return obj.card.simulate_reviews(user=obj.user)

    class Meta:
        model = ReviewDataSM2
        exclude = ("id", "user")
        read_only_fields = ("body", "computed_interval", "lapses",
                            "total_reviews", "last_reviewed", "introduced_on",
                            "review_date", "grade", "reviews",
                            "easiness_factor", "card")


class CardUserNoReviewDataSerializer(serializers.ModelSerializer):
    categories = CategoryForCardSerializer(many=True)

    class Meta:
        model = Card
        fields = ("body", "categories",)
        read_only_fields = ("body", "categories",)
