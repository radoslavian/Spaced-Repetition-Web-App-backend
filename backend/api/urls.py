from django.urls import path
from .views import (SingleCardForBackendView, ListCardsForBackendView,
                    MemorizedCards, QueuedCards, CramQueue,
                    OutstandingCards, CramSingleCard, QueuedCard,
                    MemorizedCard)

urlpatterns = [
    path("staff/cards/", ListCardsForBackendView.as_view(),
         name="list_cards"),
    path("staff/cards/<uuid:pk>/", SingleCardForBackendView.as_view(),
         name="single_card"),
    path("users/<uuid:user_id>/cards/memorized", MemorizedCards.as_view(),
         name="memorized_cards"),
    path("users/<uuid:user_id>/cards/memorized/<uuid:pk>/",
         MemorizedCard.as_view(),
         name="memorized_card"),
    path("users/<uuid:user_id>/cards/outstanding", OutstandingCards.as_view(),
         name="outstanding_cards"),
    path("users/<uuid:user_id>/cards/queued", QueuedCards.as_view(),
         name="queued_cards"),
    path("users/<uuid:user_id>/cards/queued/<uuid:pk>/", QueuedCard.as_view(),
         name="queued_card"),
    path("users/<uuid:user_id>/cards/cram-queue", CramQueue.as_view(),
         name="cram_queue"),
    path("users/<uuid:user_id>/cards/cram-queue/<uuid:card_pk>",
         CramSingleCard.as_view(),
         name="cram_single_card"),
]
