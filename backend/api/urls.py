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
    path("cards/memorized", MemorizedCards.as_view(),
         name="memorized_cards"),
    path("cards/memorized/<uuid:pk>/", MemorizedCard.as_view(),
         name="memorized_card"),
    path("cards/outstanding", OutstandingCards.as_view(),
         name="outstanding_cards"),
    path("cards/queued", QueuedCards.as_view(),
         name="queued_cards"),
    path("cards/queued/<uuid:pk>/", QueuedCard.as_view(),
         name="queued_card"),
    path("cards/cram-queue", CramQueue.as_view(),
         name="cram_queue"),
    path("cards/cram-queue/<uuid:card_pk>", CramSingleCard.as_view(),
         name="cram_single_card"),
]
