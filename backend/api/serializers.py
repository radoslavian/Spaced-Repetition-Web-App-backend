from rest_framework import serializers
from cards.models import Card, Image, CardImage, ReviewDataSM2


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ("id", "image",)


class CardForEditingSerializer(serializers.ModelSerializer):
    front_images = ImageSerializer(many=True)
    back_images = ImageSerializer(many=True)

    class Meta:
        model = Card
        fields = ("id", "front", "back", "template", "last_modified",
                  "front_images", "back_images",)
        read_only_fields = ("id", "last_modified", "front_images",
                            "back_images",)


class CardReviewDataSerializer(serializers.ModelSerializer):
    body = serializers.SerializerMethodField()

    def get_body(self, obj):
        return obj.card.body

    class Meta:
        model = ReviewDataSM2
        exclude = ("id", "user")
        read_only_fields = ("body", "computed_interval", "lapses",
                            "total_reviews", "last_reviewed", "introduced_on",
                            "review_date", "grade", "repetitions",
                            "easiness_factor", "card")


class CardUserNoReviewDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ("body",)
        read_only_fields = ("body",)
