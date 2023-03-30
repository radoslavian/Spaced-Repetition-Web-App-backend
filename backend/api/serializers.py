from rest_framework import serializers
from cards.models import Card, Image, CardImage


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
                            "back_images")


class CardForUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ("body",)
        read_only_fields = ("body",)
