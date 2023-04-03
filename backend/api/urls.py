from django.urls import path
from .views import (SingleCardForBackendView, ListCardsForBackendView,
                    SingleCardForUser)

urlpatterns = [
    path("cards/", ListCardsForBackendView.as_view(), name="list_cards"),
    path("cards/<uuid:pk>/", SingleCardForBackendView.as_view(),
         name="single_card"),
    path("users/<uuid:user_pk>/cards/<uuid:card_pk>/",
         SingleCardForUser.as_view(), name="card_for_user"),
    # path("users/<uuid:user_pk>/cards/<uuid:card_pk>/memorize",
    #      name="memorize_card"),
]
