from django.contrib.auth import get_user_model
from faker import Faker
from cards.models import Card

fake = Faker()
User = get_user_model()


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
    return [make_fake_card() for _ in range(number_of_cards)]


def make_fake_card():
    return Card.objects.create(front=fake.text(20), back=fake.text(20))


def make_fake_users(number_of_users):
    return [make_fake_user() for _ in range(number_of_users)]


def make_fake_user():
    return User.objects.create(username=fake.profile()["username"])