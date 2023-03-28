from rest_framework import serializers
from cards.models import Card, Image, CardImage


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ("id", "image",)


class CardSerializer(serializers.ModelSerializer):
    front_images = ImageSerializer(many=True)
    back_images = ImageSerializer(many=True)

    class Meta:
        model = Card
        fields = ("id", "last_modified", "front", "back", "template",
                  "front_images", "back_images",)
