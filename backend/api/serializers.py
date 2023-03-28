from rest_framework import serializers
from cards.models import Card, Image, CardImage


class CardImageSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="image.id")
    image = serializers.ReadOnlyField(source="image.image.url")

    class Meta:
        model = CardImage
        fields = ("id", "image", "side",)


class CardSerializer(serializers.ModelSerializer):
    front_images = CardImageSerializer(many=True)
    back_images = CardImageSerializer(many=True)

    class Meta:
        model = Card
        fields = ("id", "last_modified", "front", "back", "template",
                  "front_images", "back_images",)
