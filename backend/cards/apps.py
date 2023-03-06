from django.apps import AppConfig


class CardsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cards'
    default_encoding = 'utf-8'
    max_comment_len = 500
