from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from cards.models import Card, ReviewDataSM2
from cards.utils.exceptions import CardReviewDataExists
from .serializers import (CardForEditingSerializer, CardReviewDataSerializer,
                          CardUserNoReviewDataSerializer)
from .utils.helpers import get_user_or_404


# Create your views here.

class ListCardsForBackendView(ListAPIView):
    queryset = Card.objects.all().order_by("created_on")
    serializer_class = CardForEditingSerializer


class SingleCardForBackendView(RetrieveAPIView):
    queryset = Card.objects.all()
    serializer_class = CardForEditingSerializer


class SingleCardForUser(APIView):
    @staticmethod
    def _get_user_card(card_pk, user_pk):
        UserModel = get_user_model()
        card = get_object_or_404(Card, id=card_pk)
        user = get_object_or_404(UserModel, id=user_pk)
        return card, user

    @staticmethod
    def _get_review_data(card, user):
        review_data = ReviewDataSM2.objects.filter(card=card, user=user) \
            .first()
        return review_data

    def get(self, request, card_pk, user_pk):
        card, user = self._get_user_card(card_pk, user_pk)
        review_data = self._get_review_data(card, user)
        if not review_data:
            serialized_data = CardUserNoReviewDataSerializer(card)
        else:
            serialized_data = CardReviewDataSerializer(review_data)

        data = serialized_data.data
        return Response(data)

    def put(self, request, card_pk, user_pk, grade=4):
        """Putting data to the user/card url means memorizing a card.
        """
        card, user = self._get_user_card(card_pk, user_pk)
        try:
            review_data = card.memorize(user, grade=grade)
        except CardReviewDataExists:
            error_message = {
                "status_code": 400,
                "detail": f"Card with id {card.id} for user {user.username} "
                          f"id ({user.id}) is already memorized."
            }
            response = Response(error_message,
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            serialized_data = CardReviewDataSerializer(review_data).data
            response = Response(serialized_data,
                                status=status.HTTP_201_CREATED)
        return response

    def post(self, request, card_pk, user_pk, grade):
        """Posting grade to user/card ReviewData means reviewing it.
        """
        card, user = self._get_user_card(card_pk, user_pk)
        review_data = get_object_or_404(ReviewDataSM2, user=user, card=card)
        review_data.review(grade)
        serialized_data = CardReviewDataSerializer(review_data).data
        return Response(serialized_data)


class ListMemorizedCards(ListAPIView):
    serializer_class = CardReviewDataSerializer

    def get_queryset(self):
        user = get_user_or_404(self.kwargs["user_pk"])
        return ReviewDataSM2.objects.filter(user=user)\
            .order_by("introduced_on")


class ListUserNotMemorizedCards(ListAPIView):
    """list of the cards that are not yet memorized by a given user.
    """
    serializer_class = CardUserNoReviewDataSerializer

    def get_queryset(self):
        user = get_user_or_404(self.kwargs["user_pk"])
        return Card.objects.exclude(reviewing_users=user)\
            .order_by("created_on")
