from django.urls import path
from .views import (SingleCardForBackendView, ListCardsForBackendView,
                    SingleCardForUser, ListMemorizedCards,
                    ListUserNotMemorizedCards, CramQueue,
                    ListOutstandingCards, CramSingleCard)

urlpatterns = [
    # staff endpoints
    path("staff/cards/",
         ListCardsForBackendView.as_view(),
         name="list_cards"),
    path("staff/cards/<uuid:pk>/",
         SingleCardForBackendView.as_view(),
         name="single_card"),

    # regular user's endpoints
    path("cards/<uuid:card_pk>/",
         SingleCardForUser.as_view(),
         name="card_for_user"),

    # remove memorizing from this route
    path("cards/<uuid:card_pk>/grade/<int:grade>/",
         SingleCardForUser.as_view(),
         name="memorize_review_card"),

    # TODO: Reviewing:
    # POST users/<uuid:user_pk>/cards/memorized/<card_id>
    # body: { "grade": 4 }
    path("cards/memorized",
         ListMemorizedCards.as_view(),
         name="list_of_memorized_cards_for_user"),
    path("cards/outstanding",
         ListOutstandingCards.as_view(),
         name="outstanding_cards"),

    # queued cards
    # TODO: memorizing:
    # POST "users/<uuid:user_pk>/cards/queued/<card_id>"
    # body: { "grade": 4 }
    # grade should go into request body; request using POST
    # rather than PUT
    path("cards/queued",
         ListUserNotMemorizedCards.as_view(),
         name="queued_cards"),

    # cram queue
    path("cards/cram-queue",
         CramQueue.as_view(),
         name="cram_queue"),
    path("cards/cram-queue/<uuid:card_pk>",
         CramSingleCard.as_view(),
         name="cram_single_card"),
]
