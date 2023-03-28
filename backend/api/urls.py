from django.urls import path
from .views import SingleCardView, ListCardsView

urlpatterns = [
    path("cards/<uuid:pk>/", SingleCardView.as_view(), name="single_card"),
    path("cards/", ListCardsView.as_view(), name="list_cards"),
]
