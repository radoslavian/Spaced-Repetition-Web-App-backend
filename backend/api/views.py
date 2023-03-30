from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from cards.models import Card, ReviewDataSM2
from .serializers import CardForEditingSerializer, CardForUserSerializer


# Create your views here.

class ListCardsForBackendView(ListAPIView):
    queryset = Card.objects.all()
    serializer_class = CardForEditingSerializer


class SingleCardForBackendView(RetrieveAPIView):
    queryset = Card.objects.all()
    serializer_class = CardForEditingSerializer


class SingleCardForUser(APIView):
    def get(self, request, card_pk, user_pk):
        card = get_object_or_404(Card, id=card_pk)
        data = CardForUserSerializer(card).data
        return Response(data)
