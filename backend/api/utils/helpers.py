from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

User = get_user_model()


def get_user_or_404(user_id):
    return get_object_or_404(User, pk=user_id)
