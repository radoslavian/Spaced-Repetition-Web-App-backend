from django.urls import path
from .views import SingleCardForBackendView, ListCardsForBackendView, SingleCardForUser

urlpatterns = [
    path("cards/<uuid:pk>/", SingleCardForBackendView.as_view(), name="single_card"),
    path("cards/", ListCardsForBackendView.as_view(), name="list_cards"),
    path("cards/<uuid:card_pk>/users/<uuid:user_pk>/", SingleCardForUser.as_view(),
         name="card_for_user"),
]
