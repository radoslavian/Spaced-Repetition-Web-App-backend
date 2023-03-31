from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from cards.models import Card, ReviewDataSM2
from .serializers import CardForEditingSerializer, CardReviewDataSerializer, \
    CardUserNoReviewDataSerializer


# Create your views here.

class ListCardsForBackendView(ListAPIView):
    queryset = Card.objects.all()
    serializer_class = CardForEditingSerializer


class SingleCardForBackendView(RetrieveAPIView):
    queryset = Card.objects.all()
    serializer_class = CardForEditingSerializer


class SingleCardForUser(APIView):
    def get(self, request, card_pk, user_pk):
        UserModel = get_user_model()
        card = get_object_or_404(Card, id=card_pk)
        user = get_object_or_404(UserModel, id=user_pk)
        review_data = ReviewDataSM2.objects.filter(card=card, user=user)\
            .first()
        if not review_data:
            serialized_data = CardUserNoReviewDataSerializer(card)
        else:
            serialized_data = CardReviewDataSerializer(review_data)

        data = serialized_data.data
        return Response(data)
