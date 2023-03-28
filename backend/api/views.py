from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from cards.models import Card
from .serializers import CardSerializer


# Create your views here.

class ListCardsView(APIView):
    def get(self, request):
        cards = Card.objects.all()
        data = CardSerializer(cards, many=True).data
        return Response(data)


class SingleCardView(APIView):
    def get(self, request, pk):
        card = get_object_or_404(Card, id=pk)
        data = CardSerializer(card).data
        return Response(data)
