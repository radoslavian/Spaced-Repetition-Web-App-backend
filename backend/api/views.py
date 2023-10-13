import datetime
import uuid
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.urls import reverse
from django.shortcuts import get_object_or_404
from drf_multiple_model.views import FlatMultipleModelAPIView
from drf_multiple_model.pagination import MultipleModelLimitOffsetPagination
from rest_framework import status, filters, serializers
from rest_framework.exceptions import NotFound, ParseError
from rest_framework.generics import RetrieveAPIView, ListAPIView, \
    RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from cards.models import Card, CardUserData, Category
from cards.utils.exceptions import CardReviewDataExists, \
    CardsDistributionRangeExceeded
from .permissions import UserPermission
from .serializers import (CardForEditingSerializer, CardReviewDataSerializer,
                          CardUserNoReviewDataSerializer, CategorySerializer,
                          CrammedCardReviewDataSerializer)
from cards.utils.exceptions import ReviewBeforeDue
from .utils.custom_search_filters import (filter_queued_cards,
                                          filter_memorized_cards)
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
        self._user_categories = user.get_user_categories_trees()
        query_set = self.get_base_queryset()
        user_query_set = self.query_set_filter(query_set)
        return user_query_set.order_by(self.query_ordering)


class ListCardsForBackendView(ListAPIView):
    queryset = Card.objects.all().order_by("created_on")
    serializer_class = CardForEditingSerializer


class SingleCardForBackendView(RetrieveAPIView):
    queryset = Card.objects.all()
    serializer_class = CardForEditingSerializer


class LimitPagination(MultipleModelLimitOffsetPagination):
    """Paginator for AllCards view class.
    """
    default_limit = 10


class AllCards(FlatMultipleModelAPIView):
    permission_classes = [IsAuthenticated, UserPermission]
    pagination_class = LimitPagination
    # this way doesn't keep order of cards in the list
    # when memorizing cards (card memorized will be returned in
    # the different position on next reload):
    # sorting_fields = ["created_on", "body"]
    sorting_fields = ["id", "created_on"]

    def get_querylist(self):
        user_categories = self.request.user.get_user_categories_trees()
        queued_queryset = Card.objects.exclude(
            reviewing_users=self.request.user).filter(
            Q(categories__in=user_categories) |
            Q(categories__isnull=True))
        memorized_queryset = CardUserData.objects.filter(
            user=self.request.user).filter(
            Q(card__categories__in=user_categories) |
            Q(card__categories__isnull=True))

        querylist = [
            {
                "queryset": queued_queryset,
                "serializer_class": CardUserNoReviewDataSerializer,
                "label": "queued",
                "filter_fn": filter_queued_cards
            },
            {
                "queryset": memorized_queryset,
                "serializer_class": CardReviewDataSerializer,
                "label": "memorized",
                "filter_fn": filter_memorized_cards
            }
        ]
        return querylist


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
        return user_query_set.filter(
            Q(categories__in=self._user_categories) |
            Q(categories__isnull=True))


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
            Q(card__categories__in=self._user_categories) |
            Q(card__categories__isnull=True))

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

    def delete(self, request, **kwargs):
        card = get_object_or_404(Card, id=kwargs["pk"])
        try:
            card.forget(self.request.user)
        except ObjectDoesNotExist:
            return Response({
                "status_code": status.HTTP_404_NOT_FOUND,
                "detail": f"card with id {card.id} is not memorized"
            }, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

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
            Q(card__categories__in=self._user_categories) |
            Q(card__categories__isnull=True))


class CramQueue(ListAPIView):
    serializer_class = CrammedCardReviewDataSerializer
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


class SelectedCategories(APIView):
    permission_classes = [IsAuthenticated, UserPermission]

    def get(self, request, **kwargs):
        return Response(request.user.selected_categories_ids)

    @staticmethod
    def validate_uuids(uuids: list | set | tuple):
        try:
            for single_uuid in uuids:
                uuid.UUID(single_uuid)
        except ValueError:
            raise serializers.ValidationError(
                {"detail": "Malformed data: invalid UUIDs."})

    @staticmethod
    def load_categories_from_ids(category_ids):
        return [Category.objects.filter(id=category_id).first()
                for category_id in category_ids]

    def put(self, request, **kwargs):
        user = request.user
        category_ids = request.data
        self.validate_uuids(category_ids)
        selected_categories = self.load_categories_from_ids(category_ids)
        if all(selected_categories):
            user.selected_categories.set(selected_categories)
            user.save()
        else:
            raise serializers.ValidationError(
                {"detail": "Invalid input: "
                           "one or more categories was not found."})
        return Response(status=status.HTTP_204_NO_CONTENT)


class Distribution(APIView):
    permission_classes = [IsAuthenticated, UserPermission]

    def get(self, request, **kwargs):
        match kwargs.get("dynamic_part", "daily-cards"):
            case "grades":
                grades_distribution = CardUserData \
                    .get_grades_distribution(request.user)
                response = Response(grades_distribution)
            case "e-factor":
                e_factor_distribution = CardUserData \
                    .get_efactor_distribution(request.user)
                response = Response(e_factor_distribution)
            case "memorized":
                response = self.get_distribution_response(
                    self.memorization_distribution)
            case "daily-cards":
                response = self.get_distribution_response(
                    self.cards_distribution)
            case _:
                raise NotFound
        return response

    def cards_distribution(self, days_range):
        return CardUserData.get_cards_distribution(
            self.request.user, days_range)

    def memorization_distribution(self, days_range):
        return CardUserData.get_cards_memorization_distribution(
            self.request.user, days_range)

    def get_distribution_response(self, distribution_fn, default_range=3):
        days_range_string = self.request.query_params.get(
            "days-range", default_range)
        # use serializer for validation
        days_range_wrong_type = "days-range must be a positive number"
        try:
            days_range = int(days_range_string)
        except ValueError:
            raise ParseError(detail=days_range_wrong_type,
                             code=status.HTTP_400_BAD_REQUEST)
        if days_range < 0:
            raise ParseError(detail=days_range_wrong_type,
                             code=status.HTTP_400_BAD_REQUEST)
        try:
            distribution = distribution_fn(days_range)
        except CardsDistributionRangeExceeded as e:
            raise ParseError(detail=str(e), code=status.HTTP_400_BAD_REQUEST)
        return Response(distribution)


class GeneralStatistics(APIView):
    permission_classes = [IsAuthenticated, UserPermission]

    def get(self, request, **kwargs):
        number_of_memorized = CardUserData.objects.filter(
            user=request.user).count()
        total_cards = Card.objects.count()
        number_successful_reviews = CardUserData.objects.filter(
            user=request.user, grade__gt=2).count()
        if number_successful_reviews == 0:
            retention_score = None
        else:
            retention_score = round(number_successful_reviews /
                                    number_of_memorized * 100, 2)
        response = {
            "retention_score": retention_score,
            "number_of_memorized": number_of_memorized,
            "total_cards": total_cards
        }

        return Response(response, status=status.HTTP_200_OK)
