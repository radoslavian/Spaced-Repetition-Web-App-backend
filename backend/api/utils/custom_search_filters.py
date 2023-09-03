from django.db.models import Q
from cards.models import Card, CardUserData


def get_search_cards_filter(queryset_filter, card_type):
    def search_cards_filter(queryset, request, *args, **kwargs):
        search_parameter = request.query_params.get("search")
        if not search_parameter:
            return queryset

        if queryset.model is not card_type:
            raise TypeError("the queryset should be of type "
                            + str(card_type))
        else:
            return queryset_filter(search_parameter, queryset)
    return search_cards_filter


def search_queued_cards(search_parameter, queryset):
    return queryset.filter(
        Q(front__icontains=search_parameter) |
        Q(back__icontains=search_parameter) |
        Q(template__body__icontains=search_parameter))


def search_memorized_cards(search_parameter, queryset):
    return queryset.filter(
        Q(card__front__icontains=search_parameter) |
        Q(card__back__icontains=search_parameter) |
        Q(card__template__body__icontains=search_parameter))


filter_queued_cards = get_search_cards_filter(search_queued_cards, Card)
filter_memorized_cards = get_search_cards_filter(
    search_memorized_cards, CardUserData)
