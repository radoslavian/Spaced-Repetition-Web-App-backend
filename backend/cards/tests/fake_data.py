from django.contrib.auth import get_user_model
from faker import Faker
from cards.models import Card

fake = Faker()


def get_fake_card_data():
    return {
        "front": fake.text(100),
        "back": fake.text(100)
    }


def get_fake_template_data():
    return {
        "title": fake.text(60),
        "description": fake.text(300),
        "body": fake.text(300)
    }


def make_fake_cards(number_of_cards):
    cards = []
    for _ in range(number_of_cards):
        card = Card(front=fake.text(20), back=fake.text(20))
        card.save()
        cards.append(card)
    return cards


def make_fake_users(number_of_users):
    User = get_user_model()
    users = []
    for _ in range(number_of_users):
        user = User(username=fake.profile()["username"])
        user.save()
        users.append(user)
    return users
