from django.urls import path
from .views import (SingleCardForBackendView, ListCardsForBackendView,
                    SingleCardForUser, ListMemorizedCards,
                    ListUserNotMemorizedCards)

urlpatterns = [
    path("cards/", ListCardsForBackendView.as_view(), name="list_cards"),
    path("cards/<uuid:pk>/", SingleCardForBackendView.as_view(),
         name="single_card"),
    path("users/<uuid:user_pk>/cards/<uuid:card_pk>/",
         SingleCardForUser.as_view(), name="card_for_user"),
    path("users/<uuid:user_pk>/cards/<uuid:card_pk>/grade/<int:grade>/",
         SingleCardForUser.as_view(), name="memorize_review_card"),
    path("users/<uuid:user_pk>/cards/memorized", ListMemorizedCards.as_view(),
         name="list_of_memorized_cards_for_user"),
    path("users/<uuid:user_pk>/cards/queued",
         ListUserNotMemorizedCards.as_view(),
         name="list_of_not_memorized_cards_for_user"),
]
