from django.db.models import Q
from cards.models import Card, CardUserData


def filter_card(card):
    pass


def search_all_cards(queryset, request, *args, **kwargs):
    search_parameter = request.query_params.get("search")
    if not search_parameter:
        return queryset

    match queryset.model():
        case Card():
            return queryset.filter(
                Q(front__icontains=search_parameter) |
                Q(back__icontains=search_parameter) |
                Q(template__body__icontains=search_parameter)
            )
        case CardUserData():
            return queryset.filter(
                Q(card__front__icontains=search_parameter) |
                Q(card__back__icontains=search_parameter) |
                Q(card__template__body__icontains=search_parameter)
            )
        case _:
            raise TypeError("the queryset should be of "
                            + "either Card or CardUserData type")
