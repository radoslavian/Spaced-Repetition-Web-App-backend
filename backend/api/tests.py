import json
import uuid
from datetime import date, timedelta
from datetime import datetime
from random import choice
from textwrap import dedent

from cards.models import Card, CardImage, CardTemplate

if __name__ == "__main__" and __package__ is None:
    # overcoming sibling module imports problem
    # in a quick and dirty way
    from sys import path
    from os.path import dirname

    path.append(dirname(path[0]))

from django.urls import reverse
from cards.tests import FakeUsersCards, HelpersMixin


# Create your tests here.

def convert_zulu_timestamp(timestamp: str):
    return datetime.fromisoformat(
        timestamp.replace("Z", "+00:00").replace("T", " "))


class TestBackendCards(FakeUsersCards, HelpersMixin):
    def test_list_of_cards(self):  # turned off temporarily
        """List of cards with no user data.
        """
        cards = self.get_cards()
        number_of_cards = len(cards)
        response = self.client.get(reverse("list_cards"))
        cards_in_json = response.json()
        selected_card = choice(cards_in_json)
        card = Card.objects.get(id=selected_card["id"])
        expected_serialization_dict = {
            "id": str(card.id),
            "front": card.front,
            "back": card.back,
            "last_modified": card.last_modified,
            "template": card.template,
            "front_images": card.front_images,
            "back_images": card.back_images
        }
        number_of_serialized_fields = len(expected_serialization_dict)

        self.assertDictEqual(expected_serialization_dict, {
            **selected_card,
            "last_modified": convert_zulu_timestamp(
                selected_card["last_modified"])
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(cards_in_json), number_of_cards)
        self.assertEqual(len(selected_card.keys()),
                         number_of_serialized_fields)

    def test_single_card_404(self):
        """Test to response to request for a non-existent card.
        """
        fake_card_id = uuid.uuid4()
        response = self.client.get(reverse("single_card",
                                           kwargs={"pk": fake_card_id}))
        self.assertEqual(response.status_code, 404)

    def test_single_card(self):
        card, *_ = self.get_cards()
        response = self.client.get(reverse("single_card",
                                           kwargs={"pk": card.id}))
        post_response = self.client.post(reverse("single_card",
                                                 kwargs={"pk": card.id}))
        card_from_response = response.json()
        expected_serialization_dict = {
            "id": str(card.id),
            "front": card.front,
            "back": card.back,
            "last_modified": card.last_modified,
            "template": card.template,
            "front_images": card.front_images,
            "back_images": card.back_images
        }

        self.assertDictEqual(expected_serialization_dict, {
            **card_from_response,
            "last_modified": convert_zulu_timestamp(
                card_from_response["last_modified"])
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(expected_serialization_dict),
                         len(card_from_response.keys()))
        self.assertEqual(post_response.status_code, 405)

    def test_serializing_images_in_cards(self):
        """Test if front and back images are correctly serialized.
        """
        card, *_ = self.get_cards()
        first_image = self.get_image_instance()
        second_image = self.get_image_instance()
        CardImage(card=card, image=first_image, side="front").save()
        CardImage(card=card, image=first_image, side="back").save()
        CardImage(card=card, image=second_image, side="back").save()
        response = self.client.get(reverse("single_card",
                                           kwargs={"pk": card.id}))
        response_data = response.json()
        front_image_in_response = response_data["front_images"][0]
        back_image_in_response = response_data["back_images"][0]

        self.assertEqual(len(response_data["front_images"]), 1)
        self.assertEqual(len(response_data["back_images"]), 2)
        self.assertEqual(front_image_in_response["id"],
                         str(first_image.id))
        self.assertEqual(back_image_in_response["id"], str(first_image.id))
        self.assertTrue(
            str(second_image.id) not in
            [image["id"] for image in response_data["front_images"]])


class UserDataCardsTests(FakeUsersCards):
    """Tests for cards with user data and rendered content.
    """
    def test_request_no_user(self):
        """Test response for a card with non-existent user data.
        """
        fake_user_id = uuid.uuid4()
        fake_card_id = uuid.uuid4()
        response = self.client.get(
            reverse("card_for_user",
                    kwargs={"card_pk": fake_card_id,
                            "user_pk": fake_user_id}))
        self.assertEqual(response.status_code, 404)

    def test_request_non_existing_card(self):
        """Test response for a valid user.id but for a non-existent card.
        """
        user, _ = self.get_users()
        fake_card_id = uuid.uuid4()
        response = self.client.get(
            reverse("card_for_user",
                    kwargs={"card_pk": fake_card_id,
                            "user_pk": user.id}))
        self.assertEqual(response.status_code, 404)

    def test_request_for_invalid_data(self):
        """Test request where both user and card ids are invalid.
        """
        fake_user_id = uuid.uuid4()
        fake_card_id = uuid.uuid4()
        response = self.client.get(
            reverse("card_for_user",
                    kwargs={"card_pk": fake_card_id,
                            "user_pk": fake_user_id}))
        self.assertEqual(response.status_code, 404)

    def test_card_body_fallback_template(self):
        """Test user card rendering using fallback template.
        """
        card, user = self.get_card_user()
        response = self.client.get(
            reverse("card_for_user",
                    kwargs={"card_pk": card.id, "user_pk": user.id}))
        received_card_body = response.json()["body"]

        self.assertTrue("<!-- fallback card template -->"
                        in received_card_body)
        self.assertTrue(card.front in received_card_body)
        self.assertTrue(card.back in received_card_body)

    def test_card_body_template(self):
        card, user = self.get_card_user()
        template = CardTemplate()
        template.body = """<!-- test template -->
        {% extends '_base.html' %}
        {% block content %}
        <p>{{ card.front }}</p>
        <p>{{ card.back }} </p>
        {% endblock content %}
        """
        template.save()
        card.template = template
        card.save()
        response = self.client.get(
            reverse("card_for_user",
                    kwargs={"card_pk": card.id, "user_pk": user.id}))
        received_card_body = response.json()["body"]

        self.assertTrue("<!-- base template for cards-->"
                        in received_card_body)
        self.assertTrue("<!-- test template -->" in received_card_body)
        self.assertTrue(card.front in received_card_body)
        self.assertTrue(card.front in received_card_body)

    def _test_review_data(self):
        one_day = date.today() + timedelta(days=1)
        expected_review_data = {
            "introducedOn": date.today(),
            "lastReviewed": date.today(),
            "reviewDate": one_day,
            "grade": 4,
            "easinessFactor": 2.5,
            "lapses": 0,
            "totalReviews": 1,
            "reviews": 1,
            "interval": 1
        }
        card, user = self.get_card_user()
        card.memorize(user)

    def _test_projected_review_data(self):
        six_days = date.today() + timedelta(days=6)
        projected_data = {
            0: dict(easiness=1.7000000000000002,
                    interval=1,
                    reviews=0,
                    review_date=one_day),
            1: dict(easiness=1.96,
                    interval=1,
                    repetitions=0,
                    review_date=one_day)
,
            2: dict(easiness=2.1799999999999997,
                    interval=1,
                    repetitions=0,
                    review_date=one_day)
,
            3: dict(easiness=2.36,
                    interval=6,
                    repetitions=2,
                    review_date=six_days)
,
            4: dict(easiness=2.5,
                    interval=6,
                    repetitions=2,
                    review_date=six_days)
,
            5: dict(easiness=2.6,
                    interval=6,
                    repetitions=2,
                    review_date=six_days)
        }

        # test for other fields
        expected_output = {
            "cardId": str(card.id),
            "body": card_body,
            "categoryName": "category",
            "categoryId": "id",
            "comment": None,
            "ignored": "false",
            "projectedData": projected_data,
            "reviewData": review_data
        }

        self.assertDictEqual(expected_output, response_json)
