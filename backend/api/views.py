import datetime
from django.urls import reverse
from django.shortcuts import get_object_or_404
from rest_framework import status, filters
from rest_framework.generics import RetrieveAPIView, ListAPIView, \
    RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from cards.models import Card, CardUserData, Category
from cards.utils.exceptions import CardReviewDataExists
from .permissions import UserPermission
from .serializers import (CardForEditingSerializer, CardReviewDataSerializer,
                          CardUserNoReviewDataSerializer, CategorySerializer)
from cards.utils.exceptions import ReviewBeforeDue
from .utils.helpers import extract_grade, no_review_data_response


class ListAPIAbstractView(ListAPIView):
    query_ordering = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_categories = []

    def query_set_filter(self, user_query_set):
        pass

    def get_base_queryset(self):
        pass

    def get_queryset(self):
        user = self.request.user
        user_query_set = self.get_base_queryset()

        for selected_category in user.selected_categories.all():
            self._user_categories.extend(Category.get_tree(
                selected_category))
        if self._user_categories:
            user_query_set = self.query_set_filter(user_query_set)
        return user_query_set.order_by(self.query_ordering)


class ListCardsForBackendView(ListAPIView):
    queryset = Card.objects.all().order_by("created_on")
    serializer_class = CardForEditingSerializer


class SingleCardForBackendView(RetrieveAPIView):
    queryset = Card.objects.all()
    serializer_class = CardForEditingSerializer


class QueuedCards(ListAPIAbstractView):
    """list cards that are not yet memorized by a given user.
    """
    filter_backends = [filters.SearchFilter]
    search_fields = ["front", "back", "template__body"]
    serializer_class = CardUserNoReviewDataSerializer
    permission_classes = [IsAuthenticated, UserPermission]
    query_ordering = "created_on"

    def get_base_queryset(self):
        return Card.objects.exclude(reviewing_users=self.request.user)

    def query_set_filter(self, user_query_set):
        return user_query_set.filter(categories__in=self._user_categories)


class QueuedCard(RetrieveUpdateAPIView):
    serializer_class = CardUserNoReviewDataSerializer
    permission_classes = [IsAuthenticated, UserPermission]

    def get_queryset(self):
        return Card.objects.exclude(reviewing_users=self.request.user) \
            .filter(id=self.kwargs["pk"])

    def patch(self, request, **kwargs):
        """Patching grade on a queued card means memorizing it.
        """
        user = request.user
        card = get_object_or_404(Card, id=kwargs["pk"])
        grade = extract_grade(request)
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
                                status=status.HTTP_200_OK)
            response["Location"] = review_data.get_absolute_url()
        return response


class MemorizedCards(ListAPIAbstractView):
    serializer_class = CardReviewDataSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["card__front", "card__back", "card__template__body"]
    query_ordering = "introduced_on"
    permission_classes = [IsAuthenticated, UserPermission]

    def query_set_filter(self, user_query_set):
        return user_query_set.filter(
            card__categories__in=self._user_categories)

    def get_base_queryset(self):
        return CardUserData.objects.all().filter(user=self.request.user)


class MemorizedCard(RetrieveUpdateAPIView):
    serializer_class = CardReviewDataSerializer
    permission_classes = [IsAuthenticated, UserPermission]

    def get(self, request, **kwargs):
        card = get_object_or_404(Card, id=kwargs["pk"])
        card_user_data = get_object_or_404(CardUserData,
                                           user=self.request.user,
                                           card=card)
        data = self.serializer_class(card_user_data).data
        return Response(data)

    def patch(self, request, **kwargs):
        """Patching grade on a memorized card means reviewing it.
        """
        card = get_object_or_404(Card, id=self.kwargs["pk"])
        card_review_data = get_object_or_404(
            CardUserData, user=request.user, card=card)
        grade = extract_grade(request)
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
            response["Location"] = card_review_data.get_absolute_url()
        return response


class OutstandingCards(ListAPIAbstractView):
    serializer_class = CardReviewDataSerializer
    permission_classes = [IsAuthenticated, UserPermission]
    query_ordering = "introduced_on"

    def get_base_queryset(self):
        return CardUserData.objects.filter(
            user=self.request.user,
            review_date__lte=datetime.datetime.today().date()
        )

    def query_set_filter(self, user_query_set):
        return user_query_set.filter(
            card__categories__in=self._user_categories)


class CramQueue(ListAPIView):
    serializer_class = CardReviewDataSerializer
    permission_classes = [IsAuthenticated, UserPermission]

    def get_queryset(self):
        user = self.request.user
        return user.crammed_cards

    def put(self, request, *args, **kwargs):
        """Adding card to the cram queue.
        """
        card_pk = request.data["card_pk"]
        card = get_object_or_404(Card, id=card_pk)
        card_review_data = CardUserData.objects.filter(
            user=request.user, card=card).first()
        if not card_review_data:
            response = no_review_data_response(card)
        else:
            card_review_data.add_to_cram()
            serialized_data = CardReviewDataSerializer(card_review_data).data
            response = Response(serialized_data)
            response["Location"] = reverse(
                "cram_single_card",
                kwargs={"card_pk": card_review_data.card.id,
                        "user_id": card_review_data.user.id})
        return response

    def delete(self, request, **kwargs):
        """Drop cram queue for an authenticated user.
        """
        self.get_queryset().update(crammed=False)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CramSingleCard(APIView):
    permission_classes = [IsAuthenticated, UserPermission]

    def delete(self, request, **kwargs):
        card = get_object_or_404(Card, id=kwargs.get("card_pk"))
        card_review_data = CardUserData.objects.filter(
            user=request.user, card=card).first()
        if not card_review_data:
            response = no_review_data_response(card)
        else:
            card_review_data.remove_from_cram()
            response = Response(status=status.HTTP_204_NO_CONTENT)
            response["Location"] = card_review_data.get_absolute_url()
        return response


class UserCategories(RetrieveAPIView):
    permission_classes = [IsAuthenticated, UserPermission]
    queryset = Category.objects.filter(parent=None)
    serializer_class = CategorySerializer

    def get(self, request, **kwargs):
        categories = self.serializer_class(self.queryset.all(),
                                           many=True).data
        output = {
            "selected_categories": request.user.selected_categories_ids,
            "categories": categories
        }
        return Response(output)


class SelectedCategories(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, UserPermission]

    def get(self, request, **kwargs):
        return Response(request.user.selected_categories_ids)
