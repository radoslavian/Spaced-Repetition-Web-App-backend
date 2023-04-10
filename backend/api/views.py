import datetime
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
from cards.utils.exceptions import ReviewBeforeDue


def get_card_user_or_404(card_pk, user_pk):
    UserModel = get_user_model()
    card = get_object_or_404(Card, id=card_pk)
    user = get_object_or_404(UserModel, id=user_pk)
    return card, user


# Create your views here.

class ListCardsForBackendView(ListAPIView):
    queryset = Card.objects.all().order_by("created_on")
    serializer_class = CardForEditingSerializer


class SingleCardForBackendView(RetrieveAPIView):
    queryset = Card.objects.all()
    serializer_class = CardForEditingSerializer


class SingleCardForUser(APIView):
    """Returns single card with user data.
    """
    @staticmethod
    def _get_review_data(card, user):
        review_data = ReviewDataSM2.objects.filter(card=card, user=user) \
            .first()
        return review_data

    def get(self, request, card_pk):
        card = get_object_or_404(Card, id=card_pk)
        review_data = self._get_review_data(card, request.user)
        if not review_data:
            serialized_data = CardUserNoReviewDataSerializer(card)
        else:
            serialized_data = CardReviewDataSerializer(review_data)

        data = serialized_data.data
        return Response(data)

    def put(self, request, card_pk, grade=4):
        """Putting data to the user/card url means memorizing a card.
        """
        user = request.user
        card = get_object_or_404(Card, id=card_pk)
        try:
            review_data = card.memorize(user, grade=grade)
        except CardReviewDataExists:
            error_message = {
                "status_code": 400,
                "detail": f"Card with id {card.id} for user "
                          f"{user.username} id ({user.id}) "
                          f"is already memorized."
            }
            response = Response(error_message,
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            serialized_data = CardReviewDataSerializer(review_data).data
            response = Response(serialized_data,
                                status=status.HTTP_201_CREATED)
        return response

    def post(self, request, card_pk, grade):
        """Posting grade to user/card ReviewData means reviewing it.
        """
        card = get_object_or_404(Card, id=card_pk)
        user = request.user
        card_review_data = get_object_or_404(
            ReviewDataSM2, user=user, card=card)
        try:
            card_review_data.review(grade)
        except ReviewBeforeDue as e:
            response = Response({
                "status_code": status.HTTP_400_BAD_REQUEST,
                "detail": e.message
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            response = Response(
                CardReviewDataSerializer(card_review_data).data)
        return response


class ListMemorizedCards(ListAPIView):
    serializer_class = CardReviewDataSerializer

    def get_queryset(self):
        return ReviewDataSM2.objects.filter(user=self.request.user) \
            .order_by("introduced_on")


class ListOutstandingCards(ListAPIView):
    serializer_class = CardReviewDataSerializer

    def get_queryset(self):
        return ReviewDataSM2.objects.filter(
            user=self.request.user,
            review_date__lte=datetime.datetime.today().date()
        ).order_by("introduced_on")


class ListUserNotMemorizedCards(ListAPIView):
    """list of the cards that are not yet memorized by a given user.
    """
    serializer_class = CardUserNoReviewDataSerializer

    def get_queryset(self):
        return Card.objects.exclude(reviewing_users=self.request.user) \
            .order_by("created_on")


def no_review_data_response(card):
    error_message = f"The card id {card.id} is not in cram queue."
    response = Response({
        "status_code": 400,
        "detail": error_message
    }, status=status.HTTP_400_BAD_REQUEST)
    return response


class CramQueue(ListAPIView):
    serializer_class = CardReviewDataSerializer

    def get_queryset(self):
        user = self.request.user
        return user.crammed_cards

    def put(self, request):
        card_pk = request.data["card_pk"]
        card = get_object_or_404(Card, id=card_pk)
        user = request.user
        card_review_data = ReviewDataSM2.objects.filter(
            user=user, card=card).first()
        if not card_review_data:
            response = no_review_data_response(card)
        else:
            card_review_data.add_to_cram()
            serialized_data = CardReviewDataSerializer(card_review_data).data
            response = Response(serialized_data)
        return response

    def delete(self, request):
        """Drop cram queue for an authenticated user.
        """
        self.get_queryset().update(crammed=False)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CramSingleCard(APIView):
    def delete(self, request, card_pk):
        user = request.user
        card = get_object_or_404(Card, id=card_pk)
        card_review_data = ReviewDataSM2.objects.filter(
            user=user, card=card).first()
        if not card_review_data:
            response = no_review_data_response(card)
        else:
            card_review_data.remove_from_cram()
            response = Response(status=status.HTTP_204_NO_CONTENT)
        return response
