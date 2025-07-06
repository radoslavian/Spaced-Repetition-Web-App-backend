from faker import Faker

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
