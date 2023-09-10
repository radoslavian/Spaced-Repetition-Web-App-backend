import json
import random
import uuid
from math import ceil, floor
import time_machine
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from datetime import date, timedelta
from datetime import datetime
from random import choice, shuffle, randint
from cards.models import Card, CardImage, CardTemplate, Category, CardUserData
from faker import Faker
from rest_framework import status
from .utils.helpers import add_url_params

if __name__ == "__main__" and __package__ is None:
    # overcoming sibling module imports problem
    # in a quick and dirty way
    from sys import path
    from os.path import dirname

    path.append(dirname(path[0]))

from rest_framework.test import APIClient
from django.urls import reverse
from cards.tests import FakeUsersCards, HelpersMixin

fake = Faker()


def get_reverse_for(endpoint, key):
    def reverse_fn(value):
        return reverse(endpoint, kwargs={key: value})

    return reverse_fn


reverse_memorized_cards = get_reverse_for("memorized_cards", "user_id")
reverse_queued_cards = get_reverse_for("queued_cards", "user_id")
reverse_outstanding_cards = get_reverse_for("outstanding_cards", "user_id")
reverse_selected_categories = get_reverse_for("selected_categories",
                                              "user_id")
reverse_all_cards = get_reverse_for("all_cards", "user_id")


def convert_zulu_timestamp(timestamp: str):
    return datetime.fromisoformat(
        timestamp.replace("Z", "+00:00").replace("T", " "))


class ApiTestHelpersMixin(HelpersMixin):
    def setUp(self):
        self.client = APIClient()
        self.user = self.make_fake_users(1)[0]
        self.client.force_authenticate(user=self.user)


class ApiTestFakeUsersCardsMixin(ApiTestHelpersMixin, FakeUsersCards):
    def setUp(self):
        FakeUsersCards.setUp(self)
        ApiTestHelpersMixin.setUp(self)


class TestBackendCards(ApiTestFakeUsersCardsMixin):
    def test_list_of_cards_staff_forbidden(self):
        """Test if route is forbidden for unauthorized access.
        """
        # client with no authenticated user:
        client = APIClient()
        response = client.get(reverse("list_cards"))
        self.assertEqual(response.status_code, 403)

    def test_list_of_cards_staff_response_code(self):
        """Test response code for client with authenticated user.
        """
        response = self.client.get(reverse("list_cards"))
        self.assertEqual(response.status_code, 200)

    def test_list_of_cards_staff(self):
        """List of cards with no user data for staff viewing/editing.
        """
        cards = self.get_cards()
        number_of_cards = len(cards)
        response = self.client.get(reverse("list_cards"))
        cards_in_json = response.json()["results"]
        selected_card = choice(cards_in_json)
        card = Card.objects.get(id=selected_card["id"])
        expected_serialization_dict = {
            "id": str(card.id),
            "front": card.front,
            "back": card.back,
            "last_modified": card.last_modified,
            "template": card.template,
            "front_images": card.front_images,
            "categories": [],
            "back_images": card.back_images
        }
        number_of_serialized_fields = len(expected_serialization_dict)

        self.assertDictEqual(expected_serialization_dict, {
            **selected_card,
            "last_modified": convert_zulu_timestamp(
                selected_card["last_modified"])
        })
        self.assertEqual(response.json()["count"], number_of_cards)
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
            "categories": [],
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

    def test_backend_card_single_category(self):
        card, *_ = self.get_cards()
        category_name = fake.text(20)
        category = Category.objects.create(name=category_name)
        card.categories.add(category)
        card.save()
        response = self.client.get(
            reverse("single_card", kwargs={"pk": card.id}))
        response_json = response.json()

        self.assertEqual(len(response_json["categories"]), 1)
        self.assertEqual(response_json["categories"][0]["title"],
                         category_name)

    def test_card_multiple_categories(self):
        card, *_ = self.get_cards()
        category_1 = self.create_category()
        category_2 = self.create_category()
        card.categories.add(category_1, category_2)
        card.save()
        response = self.client.get(
            reverse("single_card", kwargs={"pk": card.id}))
        categories_from_response = response.json()["categories"]

        self.assertEqual(len(categories_from_response), 2)
        self.assertNotEqual(categories_from_response[0]["key"],
                            categories_from_response[1]["key"])
        self.assertNotEqual(categories_from_response[0]["title"],
                            categories_from_response[1]["title"])


class UserCardsTests(ApiTestFakeUsersCardsMixin):
    """Tests for cards with user data and rendered content.
    """

    def test_request_no_user(self):
        """Test response to an attempt to unauthorized access to a card.
        """
        client = APIClient()
        card = self.make_fake_cards(1)[0]
        response = client.get(
            reverse("memorized_card", kwargs={
                "pk": card.id,
                "user_id": self.user.id
            }))
        self.assertEqual(response.status_code, 403)

    def test_request_for_non_existing_memorized_card(self):
        """Test response to request for a non-existent card.
        """
        fake_card_id = uuid.uuid4()
        response = self.client.get(
            reverse("memorized_card",
                    kwargs={
                        "pk": fake_card_id,
                        "user_id": self.user.id
                    }))
        self.assertEqual(response.status_code, 404)

    def test_card_body_fallback_template(self):
        """Test user card rendering using fallback template.
        """
        card = self.make_fake_cards(1)[0]
        response = self.client.get(
            reverse("queued_card", kwargs={"pk": card.id,
                                           "user_id": self.user.id}))
        received_card_body = response.json()["body"]

        self.assertTrue("<!-- fallback card template -->"
                        in received_card_body)
        self.assertTrue(card.front in received_card_body)
        self.assertTrue(card.back in received_card_body)

    def test_response_for_not_memorized_card(self):
        """Tests response to request for user data for not memorized card
        using endpoint for getting a memorized card.
        """
        card = self.make_fake_cards(1)[0]
        response = self.client.get(
            reverse("memorized_card", kwargs={
                "pk": card.id,
                "user_id": self.user.id
            }))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_card_body_template(self):
        card = self.make_fake_cards(1)[0]
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
            reverse("queued_card", kwargs={"pk": card.id,
                                           "user_id": self.user.id}))
        received_card_body = response.json()["body"]

        self.assertTrue("<!-- base template for cards-->"
                        in received_card_body)
        self.assertTrue("<!-- test template -->" in received_card_body)
        self.assertTrue(card.front in received_card_body)
        self.assertTrue(card.front in received_card_body)

    def test_review_data(self):
        card = self.make_fake_cards(1)[0]
        review_data = card.memorize(self.user, 5)
        response = self.client.get(
            reverse("memorized_card", kwargs={
                "pk": card.id,
                "user_id": self.user.id
            }))
        introduced_on = review_data.introduced_on \
            .isoformat().replace("+00:00", "Z")
        expected_data = {
            "computed_interval": review_data.computed_interval,
            "lapses": review_data.lapses,
            "total_reviews": review_data.total_reviews,
            "last_reviewed": str(review_data.last_reviewed),
            "comment": None,
            "cram_link": None,
            "introduced_on": introduced_on,
            "review_date": str(review_data.review_date),
            "created_on": str(review_data.card.created_on),
            "grade": review_data.grade,
            "reviews": review_data.reviews,
            "categories": [],
            "easiness_factor": review_data.easiness_factor,
            "id": str(card.id)
        }
        received_data = response.json()
        received_data.pop("body")
        received_data.pop("projected_review_data")

        self.assertDictEqual(expected_data, received_data)

    def test_projected_review_data(self):
        card = self.make_fake_cards(1)[0]
        card_review_data = card.memorize(self.user, 4)
        with time_machine.travel(card_review_data.review_date):
            six_days = str(date.today() + timedelta(days=6))
            one_day = str(date.today() + timedelta(days=1))
            response = self.client.get(
                reverse("memorized_card",
                        kwargs={
                            "pk": card.id,
                            "user_id": self.user.id
                        }))

        expected_projected_data = {
            "0": dict(easiness=1.7000000000000002,
                      interval=1,
                      reviews=0,
                      review_date=one_day),
            "1": dict(easiness=1.96,
                      interval=1,
                      reviews=0,
                      review_date=one_day),
            "2": dict(easiness=2.1799999999999997,
                      interval=1,
                      reviews=0,
                      review_date=one_day),
            "3": dict(easiness=2.36,
                      interval=6,
                      reviews=2,
                      review_date=six_days),
            "4": dict(easiness=2.5,
                      interval=6,
                      reviews=2,
                      review_date=six_days),
            "5": dict(easiness=2.6,
                      interval=6,
                      reviews=2,
                      review_date=six_days)
        }
        received_projected_review_data = response.json(
        )["projected_review_data"]

        self.assertDictEqual(expected_projected_data,
                             received_projected_review_data)

    def test_no_projected_review_data(self):
        """Serializer shouldn't return any reviews simulation for date earlier
        than review due date.
        """
        card = self.make_fake_cards(1)[0]
        card.memorize(self.user, 4)
        response = self.client.get(reverse("memorized_card",
                                           kwargs={
                                               "pk": card.id,
                                               "user_id": self.user.id
                                           }))

        self.assertFalse(response.json()["projected_review_data"])

    def test_user_memorized_card_single_category(self):
        card = self.make_fake_cards(1)[0]
        card.memorize(self.user)
        category = self.create_category()
        card.categories.add(category)
        card.save()
        response = self.client.get(
            reverse("memorized_card",
                    kwargs={"pk": card.id,
                            "user_id": self.user.id}))
        categories_from_response = response.json()["categories"]
        category_name_from_response = categories_from_response[0]["title"]

        self.assertEqual(len(categories_from_response), 1)
        self.assertEqual(category_name_from_response, category.name)

    def test_get_forbidden_for_other_users(self):
        """Test if users cannot see each other's memorized cards.
        """
        card = self.make_fake_cards(1)[0]
        user = self.make_fake_users(1)[0]
        card.memorize(self.user)
        card.memorize(user)
        response = self.client.get(
            reverse("memorized_card", kwargs={
                "pk": card.id,
                "user_id": user.id
            }))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_memorized_card_two_categories(self):
        card = self.make_fake_cards(1)[0]
        card.memorize(self.user)
        category_1 = self.create_category()
        category_2 = self.create_category()
        card.categories.add(category_1, category_2)
        card.save()
        response = self.client.get(
            reverse("memorized_card", kwargs={
                "pk": card.id,
                "user_id": self.user.id
            }))
        categories_from_response = response.json()["categories"]

        self.assertEqual(len(categories_from_response), 2)
        self.assertNotEqual(categories_from_response[0],
                            categories_from_response[1])

    def test_user_not_memorized_card_single_category(self):
        card = self.make_fake_cards(1)[0]
        category = self.create_category()
        card.categories.add(category)
        card.save()
        response = self.client.get(
            reverse("queued_card", kwargs={"pk": card.id,
                                           "user_id": self.user.id}))
        categories_from_response = response.json()["categories"]
        category_name_from_response = response \
            .json()["categories"][0]["title"]

        self.assertEqual(len(categories_from_response), 1)
        self.assertEqual(category_name_from_response, category.name)

    def test_queued_card_two_categories(self):
        card = self.make_fake_cards(1)[0]
        category_1 = self.create_category()
        category_2 = self.create_category()
        card.categories.add(category_1, category_2)
        card.save()
        response = self.client.get(
            reverse("queued_card", kwargs={"pk": card.id,
                                           "user_id": self.user.id}))
        categories_from_response = response.json()["categories"]

        self.assertEqual(len(categories_from_response), 2)
        self.assertNotEqual(categories_from_response[0],
                            categories_from_response[1])

    def test_user_queued_card(self):
        """Test fields from the queued card: id and created_on.
        """
        card = self.make_fake_cards(1)[0]
        response = self.client.get(
            reverse("queued_card", kwargs={"pk": card.id,
                                           "user_id": self.user.id}))
        card_from_response = response.json()
        card_created_on = datetime.fromisoformat(
            card_from_response["created_on"])
        response_card_created_on = convert_zulu_timestamp(
            card_from_response["created_on"])

        self.assertEqual(str(card.id), card_from_response["id"])
        self.assertEqual(card_created_on, response_card_created_on)

    def test_access_other_user_queued_card(self):
        user = self.make_fake_users(1)[0]
        card = self.make_fake_cards(1)[0]
        response = self.client.get(
            reverse("queued_card", kwargs={"pk": card.id,
                                           "user_id": user.id}))
        response_detail = "You do not have permission to perform this action."

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        status_code_from_message = int(response.json()["status_code"])
        self.assertEqual(status_code_from_message, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()["detail"], response_detail)

    def test_access_other_user_queued_cards(self):
        user = self.make_fake_users(1)[0]
        self.make_fake_cards(1)
        response = self.client.get(
            reverse("queued_cards", kwargs={"user_id": user.id}))
        response_detail = "You do not have permission to perform this action."
        status_code_from_message = int(response.json()["status_code"])

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(status_code_from_message, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()["detail"], response_detail)


class CardMemorization(ApiTestFakeUsersCardsMixin):
    def test_memorize_card_fake_card(self):
        fake_card_id = uuid.uuid4()
        response = self.client.put(
            reverse("queued_card", kwargs={"pk": fake_card_id,
                                           "user_id": self.user.id}))
        detail = "Not found."

        self.assertFalse(response.has_header("Location"))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], detail)

    def test_memorize_card_unauthorized(self):
        """Unauthorized attempt to memorize a card.
        """
        client = APIClient()
        card, *_ = self.get_cards()
        response = client.patch(reverse("queued_card",
                                        kwargs={"pk": card.id,
                                                "user_id": self.user.id}))
        detail = "Authentication credentials were not provided."

        self.assertFalse(response.has_header("Location"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()["detail"], detail)

    def test_memorize_card_forbidden(self):
        """Attempt to memorize card from other user's queue.
        """
        card = self.make_fake_cards(1)[0]
        user = self.make_fake_users(1)[0]
        response = self.client.patch(
            reverse("queued_card",
                    kwargs={"pk": card.id,
                            "user_id": user.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_memorize_card_400(self):
        """Bad request from attempt to again memorize already memorized card.
        """
        card = self.make_fake_cards(1)[0]
        card.memorize(self.user)
        response = self.client.patch(
            reverse("queued_card", kwargs={"pk": card.id,
                                           "user_id": self.user.id}))
        detail = f"Card with id {card.id} for user {self.user.username} " \
                 f"id ({self.user.id}) is already memorized."

        self.assertFalse(response.has_header("Location"))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status_code"], 400)
        self.assertEqual(response.json()["detail"], detail)

    def test_memorize_success(self):
        grade = 1
        card = self.make_fake_cards(1)[0]
        response = self.client.patch(
            reverse("queued_card", kwargs={"pk": card.id,
                                           "user_id": self.user.id}),
            json.dumps({"grade": grade}),
            content_type="application/json")
        print(json.dumps(response.json(), indent=3))
        location_header = response.get("Location")
        user_card_data = CardUserData.objects.get(card=card, user=self.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(location_header, user_card_data.get_absolute_url())
        self.assertEqual(response.json()["grade"], grade)

    def test_memorize_success_no_grade(self):
        """Successful memorization with default grade.
        """
        default_grade = 4
        card = self.make_fake_cards(1)[0]
        response = self.client.patch(
            reverse("queued_card", kwargs={"pk": card.id,
                                           "user_id": self.user.id}))
        location_header = response.get("Location")
        user_card_data = CardUserData.objects.get(card=card, user=self.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(location_header, user_card_data.get_absolute_url())
        self.assertEqual(response.json()["grade"], default_grade)

    def test_forgetting_card_success(self):
        card = self.make_fake_cards(1)[0]
        card.memorize(self.user)
        request_url = reverse("memorized_card",
                              kwargs={"pk": card.id,
                                      "user_id": self.user.id})
        response_delete = self.client.delete(request_url)
        memorized_card = lambda: CardUserData.objects.get(card=card,
                                                          user=self.user)

        self.assertEqual(response_delete.status_code,
                         status.HTTP_204_NO_CONTENT)
        self.assertRaises(ObjectDoesNotExist, memorized_card)

    def test_forgetting_not_memorized(self):
        """Response to attempt to forget not memorized card.
        """
        card = self.make_fake_cards(1)[0]
        request_url = reverse("memorized_card",
                              kwargs={"pk": card.id,
                                      "user_id": self.user.id})
        response_delete = self.client.delete(request_url)
        expected_reason_phrase = f"card with id {card.id} is not memorized"
        response_reason_phrase = response_delete.json()["detail"]

        self.assertEqual(response_delete.status_code,
                         status.HTTP_404_NOT_FOUND)
        self.assertEqual(expected_reason_phrase, response_reason_phrase)

    def test_forgetting_no_card(self):
        """Response to attempt to forget non-existent card.
        """
        card_id = "337f4ea1-9159-49bd-a429-619e1a8ee052"
        request_url = reverse("memorized_card",
                              kwargs={"pk": card_id,
                                      "user_id": self.user.id})
        response_delete = self.client.delete(request_url)
        expected_reason_phrase = "Not found."
        response_reason_phrase = response_delete.json()["detail"]

        self.assertEqual(response_delete.status_code,
                         status.HTTP_404_NOT_FOUND)
        self.assertEqual(expected_reason_phrase, response_reason_phrase)


class ReviewingCard(ApiTestFakeUsersCardsMixin):
    def test_review_forbidden_for_other_users(self):
        """Test if users cannot review each other's cards.
        """
        card = self.make_fake_cards(1)[0]
        user = self.make_fake_users(1)[0]
        user_data = card.memorize(self.user)
        card.memorize(user)
        with time_machine.travel(user_data.review_date):
            response = self.client.patch(
                reverse("memorized_card", kwargs={
                    "pk": card.id,
                    "user_id": user.id
                }),
                json.dumps({"grade": 2}), content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_card_not_found(self):
        fake_card_id = uuid.uuid4()
        response = self.client.patch(
            reverse("memorized_card", kwargs={
                "pk": fake_card_id,
                "user_id": self.user.id
            }),
            json.dumps({"grade": 3}), content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.has_header("Location"))
        self.assertEqual(response.json()["detail"], "Not found.")

    def test_grading(self):
        card = self.make_fake_cards(1)[0]
        review_card_data = card.memorize(self.user)
        review_grade = 3
        with time_machine.travel(review_card_data.review_date):
            response = self.client.patch(
                reverse("memorized_card", kwargs={
                    "user_id": self.user.id,
                    "pk": card.id
                }),
                json.dumps({"grade": review_grade}),
                content_type="application/json")
        response_json = response.json()
        location_header = response.get("Location")

        self.assertEqual(location_header, review_card_data.get_absolute_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_json["reviews"], 2)
        self.assertEqual(response_json["grade"], review_grade)

    def test_grading_before_review_date(self):
        """Test response to attempt to review card before it's review date.
        """
        card = self.make_fake_cards(1)[0]
        card.memorize(self.user)
        response = self.client.patch(
            reverse("memorized_card", kwargs={
                "pk": card.id,
                "user_id": self.user.id
            }),
            json.dumps({"grade": 3}),
            content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.has_header("Location"))
        self.assertEqual(response.json()["status_code"],
                         status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["detail"],
                         "Reviewing before card's due review date "
                         "is forbidden.")


class ListOfCardsForUser(ApiTestHelpersMixin, TestCase):
    def test_memorized_no_permission(self):
        cards = self.make_fake_cards(2)
        user = self.make_fake_users(1)[0]
        for card in cards:
            card.memorize(user)
        response = self.client.get(reverse_memorized_cards(user.id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_of_memorized_cards(self):
        """General test for getting list of memorized cards for an app user.
        """
        NUMBER_OF_CARDS = 15
        half_of_cards = ceil(NUMBER_OF_CARDS / 2)
        cards = self.make_fake_cards(NUMBER_OF_CARDS)
        user_2 = self.make_fake_users(1)[0]
        shuffle(cards)
        memorized_cards = [card.memorize(self.user)
                           for card in cards[:half_of_cards]]
        cards[-1].memorize(user_2)
        response = self.client.get(reverse_memorized_cards(self.user.id))
        response_content = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_content["count"], half_of_cards)
        self.assertFalse(response_content["results"][0]["cram_link"])
        self.assertEqual(response_content["results"][0]["body"],
                         memorized_cards[0].card.body)

    def test_get_list_of_memorized_cards_unauthorized_user(self):
        cards = self.make_fake_cards(2)
        control_user = self.make_fake_users(1)[0]
        for card in cards:
            card.memorize(control_user)
        client = APIClient()
        response = client.get(
            reverse("memorized_cards", kwargs={"user_id": self.user.id}))
        control_response = self.client.get(
            reverse("memorized_cards", kwargs={"user_id": control_user.id}))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(control_response.status_code,
                         status.HTTP_403_FORBIDDEN)

    def test_list_of_queued_unauthorized(self):
        client = APIClient()
        self.make_fake_cards(2)
        response = client.get(reverse("queued_cards",
                                      kwargs={"user_id": self.user.id}))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_of_queued_cards(self):
        NUMBER_OF_CARDS = 10
        half_of_cards = ceil(NUMBER_OF_CARDS / 2)
        cards = self.make_fake_cards(NUMBER_OF_CARDS)
        user_1 = self.make_fake_users(1)[0]
        memorized_cards = [card.memorize(self.user)
                           for card in cards[:half_of_cards]]
        not_memorized_cards = cards[half_of_cards:]
        cards[-1].memorize(user_1)
        number_of_queued_cards = len(not_memorized_cards)

        response = self.client.get(reverse("queued_cards",
                                           kwargs={"user_id": self.user.id}))
        response_body = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_body["count"], number_of_queued_cards)
        self.assertEqual(not_memorized_cards[0].body,
                         response_body["results"][0]["body"])

    def test_list_of_queued_cards_single_user(self):
        """Test if only cards for currently authorized user are returned.
        """
        NUMBER_OF_CARDS = 2
        card_1, card_2 = self.make_fake_cards(NUMBER_OF_CARDS)
        user_2 = self.make_fake_users(1)[0]
        card_1.memorize(self.user)
        card_2.memorize(user_2)
        response = self.client.get(reverse("queued_cards",
                                           kwargs={"user_id": self.user.id}))
        response_results = response.json()["results"]

        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(card_2.body, response_results[0]["body"])

    def test_sum_memorized_queued_cards(self):
        """Test if number of cards for both endpoints:
        for memorized and not memorized cards - equals total number of cards.
        """
        NUMBER_OF_CARDS = 20
        portion_of_cards = ceil(NUMBER_OF_CARDS / 2)
        cards = self.make_fake_cards(NUMBER_OF_CARDS)
        for card in cards[:portion_of_cards]:
            card.memorize(self.user)
        response_not_memorized = self.client.get(
            reverse("queued_cards",
                    kwargs={"user_id": self.user.id}))
        response_memorized = self.client.get(
            reverse_memorized_cards(self.user.id))

        number_of_memorized_cards = response_memorized.json()["count"]
        number_of_queued_cards = response_not_memorized.json()["count"]

        self.assertEqual(sum([number_of_memorized_cards,
                              number_of_queued_cards]), NUMBER_OF_CARDS)

    def test_outstanding_cards(self):
        """Test retrieving outstanding cards.
        """
        NUMBER_OF_NOT_MEMORIZED_CARDS = 2
        NUMBER_OF_MEMORIZED_CARDS = 3
        NUMBER_OF_REVIEWED_CARDS = 4
        due_for_memorized = date.today() + timedelta(days=3)
        due_for_review = due_for_memorized + timedelta(days=6)

        not_memorized_cards = self.make_fake_cards(
            NUMBER_OF_NOT_MEMORIZED_CARDS)
        memorized_cards = self.make_fake_cards(NUMBER_OF_MEMORIZED_CARDS)
        reviewed_cards = self.make_fake_cards(NUMBER_OF_REVIEWED_CARDS)

        for card in memorized_cards:
            card.memorize(self.user)

        for card in reviewed_cards:
            card_review_data = card.memorize(self.user)
            with time_machine.travel(card_review_data.review_date):
                card_review_data.review(4)

        with time_machine.travel(due_for_memorized):
            response_cards_memorized = self.client.get(
                reverse("outstanding_cards",
                        kwargs={"user_id": self.user.id}))

        with time_machine.travel(due_for_review):
            response_cards_for_review = self.client.get(
                reverse("outstanding_cards",
                        kwargs={"user_id": self.user.id}))
        card_for_review_body = response_cards_for_review.json()[
            "results"][0]["body"]

        self.assertEqual(response_cards_memorized.json()["count"],
                         NUMBER_OF_MEMORIZED_CARDS)
        self.assertEqual(response_cards_for_review.json()["count"],
                         NUMBER_OF_MEMORIZED_CARDS + NUMBER_OF_REVIEWED_CARDS)
        self.assertEqual(card_for_review_body, memorized_cards[0].body)

    def test_outstanding_cards_unauthorized(self):
        """Attempt to download outstanding cards without authorization.
        """
        client = APIClient()
        response = client.get(reverse("outstanding_cards",
                                      kwargs={"user_id": self.user.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_outstanding_cards_another_user(self):
        """Attempt to access list of outstanding cards from another user.
        """
        card = self.make_fake_cards(1)[0]
        user = self.make_fake_users(1)[0]
        card.memorize(user, 2)
        response = self.client.get(reverse("outstanding_cards",
                                           kwargs={"user_id": user.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ListAllCards(ApiTestHelpersMixin, TestCase):
    """Tests for endpoint returning all cards:
    /users/{id}/cards/
    """

    def test_sorting(self):
        """List for "all cards" should be ordered (sorted) by
        the card creation date.
        """
        # needs work
        card_1, card_2 = self.make_fake_cards(2)
        card_1.memorize(self.user)
        response = self.client.get(reverse_all_cards(self.user.id))
        results = response.json()["results"]
        self.assertEqual(results[0]["id"], str(card_1.id))

    def test_cards_memorized_queued(self):
        """Test making list composed of both memorized and queued cards.
        """
        card_memorized, card_queued = self.make_fake_cards(2)
        card_memorized.memorize(self.user)
        response = self.client.get(reverse_all_cards(self.user.id))
        response_json = response.json()
        card_ids = [card["id"] for card in response_json["results"]]

        self.assertTrue(str(card_memorized.id) in card_ids)
        self.assertTrue(str(card_queued.id) in card_ids)
        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(response_json["overall_total"], 2)

    def test_memorized_only(self):
        """Test endpoint when only memorized card is to be returned.
        """
        card = self.make_fake_cards(1)[0]
        card.memorize(self.user)
        response = self.client.get(reverse_all_cards(self.user.id))
        response_json = response.json()

        self.assertEqual(response_json["overall_total"], 1)

    def test_queued_only(self):
        card = self.make_fake_cards(1)[0]
        response = self.client.get(reverse_all_cards(self.user.id))
        response_json = response.json()

        self.assertEqual(response_json["overall_total"], 1)

    def test_cards_with_categories_selected(self):
        """Test for returning cards with categories attached and user-selected
        category.
        """
        category = Category(name="main category")
        category.save()
        self.user.selected_categories.add(category)
        card_memorized, card_queued = self.make_fake_cards(2)
        card_memorized.categories.add(category)
        card_queued.categories.add(category)
        card_queued.save()
        card_memorized.save()
        response = self.client.get(reverse_all_cards(self.user.id))
        response_json = response.json()

        self.assertEqual(response_json["overall_total"], 2)

    def test_cards_with_categories_unselected(self):
        """Cards have categories attached, user has different (than cards')
        category selected.
        """
        card_category = Category(name="card category")
        user_category = Category(name="user category")
        card_category.save()
        user_category.save()
        self.user.selected_categories.add(user_category)
        card_memorized, card_queued = self.make_fake_cards(2)
        card_memorized.categories.add(card_category)
        card_queued.categories.add(card_category)
        card_queued.save()
        card_memorized.save()
        response = self.client.get(reverse_all_cards(self.user.id))
        response_json = response.json()

        self.assertEqual(response_json["overall_total"], 0)


class Cram(ApiTestHelpersMixin, TestCase):
    def test_adding_to_cram_success(self):
        card_1 = self.make_fake_cards(1)[0]
        user_2 = self.make_fake_users(1)[0]
        card_1.memorize(self.user, 5)
        card_1.memorize(user_2, 5)
        card_1_data = {"card_pk": card_1.id}
        response = self.client.put(reverse(
            "cram_queue", kwargs={"user_id": self.user.id}),
            data=card_1_data)
        response_card_body = response.json()["body"]
        response_to_user_2 = self.client.put(reverse(
            "cram_queue", kwargs={"user_id": user_2.id}),
            data=card_1_data)

        # should return resource's location within cram queue
        # sending DELETE to this url shall remove element from the cram queue
        card_1_location = reverse("cram_single_card",
                                  kwargs={**card_1_data,
                                          "user_id": str(self.user.id)})

        self.assertEqual(response_to_user_2.status_code,
                         status.HTTP_403_FORBIDDEN)
        self.assertTrue(response.status_code, status.HTTP_200_OK)
        self.assertEqual(card_1_location, response["Location"])
        self.assertEqual(len(self.user.crammed_cards), 1)
        self.assertEqual(card_1.body, response_card_body)

    def test_adding_to_cram_bad_request(self):
        card = self.make_fake_cards(1)[0]
        card_request = {"card_pk": card.id}
        response = self.client.put(
            reverse("cram_queue",
                    kwargs={"user_id": self.user.id}), data=card_request)
        response_json = response.json()
        error_detail = f"The card id {card.id} is not in cram queue."

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.has_header("Location"))
        self.assertEqual(response_json["status_code"], 400)
        self.assertEqual(response_json["detail"], error_detail)

    def test_retrieving_cram_queue(self):
        NUMBER_OF_CARDS = 5
        cards = self.make_fake_cards(NUMBER_OF_CARDS)
        cards_ids = [str(card.id) for card in cards]
        user = self.make_fake_users(1)[0]
        user_cards = self.make_fake_cards(NUMBER_OF_CARDS)
        user_cards_ids = [str(card.id) for card in user_cards]
        for card in user_cards:
            card.memorize(user, 2)
        for card in cards:
            card.memorize(self.user, 3)
        response = self.client.get(reverse(
            "cram_queue",
            kwargs={"user_id": str(self.user.id)}))
        response_other_user = self.client.get(reverse(
            "cram_queue",
            kwargs={"user_id": str(user.id)}))
        response_json = response.json()
        card_selected_from_response = choice(response_json["results"])
        retrieved_card_id = card_selected_from_response["id"]
        cram_link = reverse("cram_single_card",
                            kwargs={"card_pk": str(retrieved_card_id),
                                    "user_id": str(self.user.id)})

        self.assertEqual(response_other_user.status_code,
                         status.HTTP_403_FORBIDDEN)
        self.assertEqual(card_selected_from_response["cram_link"], cram_link)
        self.assertTrue(retrieved_card_id in cards_ids)
        self.assertFalse(retrieved_card_id in user_cards_ids)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_json["count"], NUMBER_OF_CARDS)

    def test_adding_to_another_users_cram(self):
        """Attempt to add card to another user's cram is forbidden.
        """
        card = self.make_fake_cards(1)[0]
        user = self.make_fake_users(1)[0]
        card.memorize(user, 3)
        response = self.client.put(reverse(
            "cram_queue", kwargs={"user_id": user.id}),
            data={"card_pk": card.id})
        message_status_code = int(response.json()["status_code"])
        response_detail = "You do not have permission to perform this action."

        self.assertEqual(message_status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()["detail"], response_detail)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_access_to_another_user_cram(self):
        """Attempt to retrieve other user's cram, which is forbidden.
        """
        card = self.make_fake_cards(1)[0]
        user = self.make_fake_users(1)[0]
        user_data = card.memorize(user, 3)
        user_data.add_to_cram()
        response = self.client.get(
            reverse("cram_queue", kwargs={"user_id": user.id}))
        response_message = "You do not have permission to perform" \
                           " this action."

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()["detail"], response_message)
        status_code_from_json = int(response.json()["status_code"])
        self.assertEqual(status_code_from_json, status.HTTP_403_FORBIDDEN)

    def test_removing_card_from_cram_400(self):
        """Test response to attempt to delete not memorized card
        with user-data.
        """
        card = self.make_fake_cards(1)[0]
        response = self.client.delete(
            reverse("cram_single_card",
                    kwargs={"card_pk": card.id,
                            "user_id": str(self.user.id)}))
        response_json = response.json()
        error_detail = f"The card id {card.id} is not " \
                       f"in cram queue."

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.has_header("Location"))
        self.assertEqual(response_json["status_code"],
                         status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_json["detail"], error_detail)

    def test_removing_card_from_cram(self):
        card = self.make_fake_cards(1)[0]
        card_user_cata = card.memorize(self.user)
        response = self.client.delete(
            reverse("cram_single_card",
                    kwargs={"card_pk": card.id,
                            "user_id": str(self.user.id)}))
        location = card_user_cata.get_absolute_url()

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(location, response["Location"])

    def test_delete_from_cram_fake_user(self):
        """Attempt to drop a card from cram using fake user's id.
        """
        card = self.make_fake_cards(1)[0]
        fake_user_id = uuid.uuid4()
        response = self.client.delete(
            reverse("cram_single_card",
                    kwargs={"card_pk": card.id,
                            "user_id": fake_user_id}))

        # add assertions for status codes and message in json output
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_deleting_from_cram_forbidden(self):
        """Attempt to drop another user's crammed card.
        """
        card = self.make_fake_cards(1)[0]
        user = self.make_fake_users(1)[0]
        card_user_data = card.memorize(user, 3)
        card_user_data.add_to_cram()
        response = self.client.delete(
            reverse("cram_single_card",
                    kwargs={"card_pk": card.id,
                            "user_id": user.id}))
        expected_response_detail = "You do not have permission to perform" \
                                   " this action."

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response_json_status_code = int(response.json()["status_code"])
        self.assertEqual(response.json()["detail"],
                         expected_response_detail)
        self.assertEqual(response_json_status_code,
                         status.HTTP_403_FORBIDDEN)

    def test_post_not_allowed(self):
        """Post method shouldn't be allowed for cram queue route.
        """
        card = self.make_fake_cards(1)[0]
        card.memorize(self.user)
        response = self.client.post(
            reverse("cram_single_card",
                    kwargs={"card_pk": card.id,
                            "user_id": str(self.user.id)}))

        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertFalse(response.has_header("Location"))

    def test_deleting_user_cram_queue(self):
        """Test deleting all cards from user's cram queue.
        """
        cards = self.make_fake_cards(5)
        other_cards = self.make_fake_cards(5)
        other_user = self.make_fake_users(1)[0]
        cards_userdata = []
        other_cards_userdata = []
        for card in cards:
            card_userdata = card.memorize(self.user)
            card_userdata.add_to_cram()
            cards_userdata.append(card_userdata)
        for card in other_cards:
            card_userdata = card.memorize(other_user)
            card_userdata.add_to_cram()
            other_cards_userdata.append(card_userdata)

        response = self.client.delete(
            reverse("cram_queue", kwargs={"user_id": self.user.id}))
        response_to_other_user = self.client.delete(
            reverse("cram_queue", kwargs={"user_id": other_user.id}))
        for card in cards_userdata + other_cards_userdata:
            card.refresh_from_db()

        self.assertEqual(response_to_other_user.status_code,
                         status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(all([card.crammed for card in cards_userdata]))
        self.assertTrue(all([card.crammed
                             for card in other_cards_userdata]))

    def test_deleting_another_users_cram_queue(self):
        cards = self.make_fake_cards(2)
        user = self.make_fake_users(1)[0]
        for card in cards:
            card_user_data = card.memorize(user, 3)
            card_user_data.add_to_cram()
        response = self.client.delete(
            reverse("cram_queue", kwargs={"user_id": user.id}))
        expected_response_detail = "You do not have permission to perform" \
                                   " this action."

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # obtaining any json data before checking response status code
        # might have caused error before test's failing
        response_json_status_code = int(response.json()["status_code"])
        self.assertEqual(response.json()["detail"],
                         expected_response_detail)
        self.assertEqual(response_json_status_code,
                         status.HTTP_403_FORBIDDEN)

    def test_crammed_card_no_projected_reviews(self):
        """Crammed cards shouldn't have projected intervals.
        """
        card = self.make_fake_cards(1)[0]
        card_review_data = card.memorize(self.user, 1)
        with time_machine.travel(card_review_data.review_date):
            response = self.client.get(reverse(
                "cram_queue",
                kwargs={"user_id": str(self.user.id)}))
        card_from_response = response.json()["results"][0]

        self.assertRaises(
            KeyError, lambda: card_from_response["projected_review_data"])


class AllCardsFiltering(ApiTestHelpersMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.memorized_front_text = ("Lorem ipsum dolor sit amet, "
                                     "consectetur adipiscing elit. Cras "
                                     "porttitor mauris ut odio auctor "
                                     "ullamcorper.")
        self.memorized_back_text = ("Curabitur eleifend vitae nunc dapibus "
                                    "fringilla. Curabitur tincidunt "
                                    "pharetra ante.")
        self.queued_front_text = ("Maecenas lobortis sapien non consectetur "
                                  "mattis. Suspendisse luctus fringilla "
                                  "lectus vel cursus.")
        self.queued_back_text = ("Suspendisse et velit et quam eleifend "
                                 "mattis. Nam vehicula est lectus, "
                                 "ut lobortis libero luctus non.")
        self.memorized_card = Card(front=self.memorized_front_text,
                                   back=self.memorized_back_text)
        self.queued_card = Card(front=self.queued_front_text,
                                back=self.queued_back_text)
        self.template_search_text = ("<p>Example's template body and search "
                                     "text.</p>")
        template_body = """{% extends "_base.html" %}
{% block content %}
<div class="card-question">
<p></p>
<p>{{ card.front|safe }}</p>
</div>
<hr />
<div class="card-answer">
<p>{{ card.back|safe }}</p>
</div>
{% endblock content %}
""" + self.template_search_text
        self.template = CardTemplate.objects.create(
            title="test template",
            description="test template's description",
            body=template_body
        )
        self.template.save()
        self.memorized_card.template = self.template
        self.memorized_card.save()
        self.queued_card.save()
        self.memorized_card.memorize(self.user)

    def test_searching_front_memorized(self):
        url = add_url_params(reverse("all_cards",
                                     kwargs={"user_id": self.user.id}),
                             {"search": self.memorized_front_text})
        response = self.client.get(url)
        response_json = response.json()

        self.assertEqual(response_json["overall_total"], 1)
        self.assertEqual(response_json["results"][0]["id"],
                         str(self.memorized_card.id))
        self.assertTrue(response_json["results"][0]["grade"])

    def test_searching_front_queued(self):
        url = add_url_params(reverse("all_cards",
                                     kwargs={"user_id": self.user.id}),
                             {"search": self.queued_front_text})
        response = self.client.get(url)
        response_json = response.json()

        self.assertEqual(response_json["overall_total"], 1)
        self.assertEqual(response_json["results"][0]["id"],
                         str(self.queued_card.id))
        self.assertRaises(KeyError,
                          lambda: response_json["results"][0]["grade"])

    def test_searching_back_memorized(self):
        url = add_url_params(reverse("all_cards",
                                     kwargs={"user_id": self.user.id}),
                             {"search": self.memorized_back_text})
        response = self.client.get(url)
        response_json = response.json()

        self.assertEqual(response_json["overall_total"], 1)
        self.assertEqual(response_json["results"][0]["id"],
                         str(self.memorized_card.id))

    def test_searching_back_queued(self):
        url = add_url_params(reverse("all_cards",
                                     kwargs={"user_id": self.user.id}),
                             {"search": self.queued_back_text})
        response = self.client.get(url)
        response_json = response.json()

        self.assertEqual(response_json["overall_total"], 1)
        self.assertEqual(response_json["results"][0]["id"],
                         str(self.queued_card.id))

    def test_searching_by_template(self):
        url = add_url_params(reverse("all_cards",
                                     kwargs={"user_id": self.user.id}),
                             {"search": self.template_search_text})
        response = self.client.get(url)
        response_json = response.json()

        self.assertEqual(response_json["overall_total"], 1)
        self.assertEqual(response_json["results"][0]["id"],
                         str(self.memorized_card.id))


class MemorizedCardsFiltering(ApiTestHelpersMixin, TestCase):
    """Test DRF's searching-filtering functionality for memorized cards.
    """

    def setUp(self):
        super().setUp()
        self.cards = self.make_fake_cards(5)
        self.selected_card = choice(self.cards)
        for card in self.cards:
            card.memorize(self.user)

    def test_user_search_permission(self):
        """Check if a user is forbidden from accessing another user's cards.
        """
        control_user = self.make_fake_users(1)[0]
        self.cards[0].memorize(control_user)
        url_control_user = add_url_params(
            reverse_memorized_cards(control_user.id),
            {"search": self.selected_card.front})
        response = self.client.get(url_control_user)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_card_search_front(self):
        url_user = add_url_params(reverse_memorized_cards(self.user.id),
                                  {"search": self.selected_card.front})
        response_user = self.client.get(url_user)
        response_json = response_user.json()

        self.assertEqual(response_user.status_code, status.HTTP_200_OK)
        self.assertEqual(response_user.json()["count"], 1)
        self.assertEqual(response_json["results"][0]["id"],
                         str(self.selected_card.id))

    def test_card_back_search(self):
        url = add_url_params(reverse_memorized_cards(self.user.id),
                             {"search": self.selected_card.back})
        response = self.client.get(url)
        response_json = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_json["count"], 1)
        self.assertEqual(response_json["results"][0]["id"],
                         str(self.selected_card.id))

    def test_card_template_search(self):
        other_user = self.make_fake_users(1)[0]
        for card in self.cards:
            card.memorize(other_user)
        template_text = fake.text(20)
        template = CardTemplate(title=fake.text(10),
                                description=fake.text(10),
                                body=f"{template_text}")
        template.save()
        self.selected_card.template = template
        self.selected_card.save()
        url = add_url_params(reverse_memorized_cards(self.user.id),
                             {"search": template_text})
        url_for_other_user = add_url_params(
            reverse_memorized_cards(other_user.id),
            {"search": template_text})
        response = self.client.get(url)
        response_for_other_user = self.client.get(url_for_other_user)
        response_json = response.json()

        self.assertEqual(response_for_other_user.status_code,
                         status.HTTP_403_FORBIDDEN)
        self.assertEqual(response_json["count"], 1)
        self.assertEqual(response_json["results"][0]["id"],
                         str(self.selected_card.id))


class QueuedCardsFiltering(ApiTestHelpersMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.cards = self.make_fake_cards(5)
        self.selected_card = choice(self.cards)

    def test_card_front(self):
        url = add_url_params(reverse("queued_cards",
                                     kwargs={"user_id": self.user.id}),
                             {"search": self.selected_card.front})
        response = self.client.get(url)
        response_json = response.json()

        self.assertEqual(response_json["count"], 1)
        self.assertEqual(response_json["results"][0]["id"],
                         str(self.selected_card.id))

    def test_card_back(self):
        url = add_url_params(reverse("queued_cards",
                                     kwargs={"user_id": self.user.id}),
                             {"search": self.selected_card.back})
        response = self.client.get(url)
        response_json = response.json()

        self.assertEqual(response_json["count"], 1)
        self.assertEqual(response_json["results"][0]["id"],
                         str(self.selected_card.id))

    def test_card_template(self):
        template_text = fake.text(20)
        template = CardTemplate(title=fake.text(10),
                                description=fake.text(10),
                                body=f"{template_text}")
        template.save()
        self.selected_card.template = template
        self.selected_card.save()

        url = add_url_params(reverse("queued_cards",
                                     kwargs={"user_id": self.user.id}),
                             {"search": template_text})
        response = self.client.get(url)
        response_json = response.json()

        self.assertEqual(response_json["count"], 1)
        self.assertEqual(response_json["results"][0]["id"],
                         str(self.selected_card.id))


class CardsMultipleSubcategories(ApiTestHelpersMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.parent = Category(name="first parent category")
        self.parent.save()
        self.first_sub_category = Category(name="first sibling category",
                                           parent=self.parent)
        self.first_sub_category.save()
        self.second_sub_category = Category(name="second sibling category",
                                            parent=self.parent)
        self.second_sub_category.save()
        self.third_sub_category = Category(name="third sibling category",
                                           parent=self.parent)
        self.third_sub_category.save()
        self.card_1, self.card_2, self.card_3 = self.make_fake_cards(3)
        self.card_1.categories.add(self.first_sub_category)
        self.card_2.categories.add(self.second_sub_category)
        self.card_2.categories.add(self.third_sub_category)

    def memorize_cards(self):
        for card in self.card_1, self.card_2, self.card_3:
            card.memorize(self.user)

    def test_parent_category_selected_memorized_cards(self):
        self.memorize_cards()
        self.user.selected_categories.add(self.parent)
        self.user.save()
        response = self.client.get(reverse_memorized_cards(self.user.id))

        self.assertEqual(response.json()["count"], 3)

    def test_parent_category_selected_outstanding_cards(self):
        self.memorize_cards()
        self.user.selected_categories.add(self.parent)
        self.user.save()
        travel_date = datetime.today() + timedelta(days=4)
        with time_machine.travel(travel_date):
            response = self.client.get(
                reverse_outstanding_cards(self.user.id))

        self.assertEqual(response.json()["count"], 3)

    def test_parent_category_selected_queued_cards(self):
        self.user.selected_categories.add(self.parent)
        self.user.save()
        response = self.client.get(reverse_queued_cards(self.user.id))

        self.assertEqual(response.json()["count"], 3)

    def test_single_subcategory_selected_memorized_cards(self):
        self.memorize_cards()
        self.user.selected_categories.set([self.first_sub_category])
        self.user.save()
        # additional card attached to the root category
        card = self.make_fake_cards(1)[0]
        card.categories.add(self.parent)
        card.save()
        card.memorize(self.user)
        response_all_cards = self.client.get(
            reverse_memorized_cards(self.user.id))
        response_card_1 = self.client.get(
            reverse("memorized_card", kwargs={
                "user_id": self.user.id,
                "pk": self.card_1.id
            }))

        self.assertDictEqual(response_card_1.json(),
                             response_all_cards.json()["results"][0])
        self.assertEqual(response_all_cards.json()["count"], 1)
        self.assertEqual(response_all_cards.json()["results"][0]["id"],
                         str(self.card_1.id))

    def test_single_subcategory_selected_outstanding_cards(self):
        self.memorize_cards()
        self.user.selected_categories.set([self.first_sub_category])
        self.user.save()
        # additional card attached to the root category
        card = self.make_fake_cards(1)[0]
        card.categories.add(self.parent)
        card.save()
        card.memorize(self.user)
        travel_time = datetime.today() + timedelta(days=4)
        with time_machine.travel(travel_time):
            response_all_cards = self.client.get(
                reverse_outstanding_cards(self.user.id))
            response_card_1 = self.client.get(
                reverse("memorized_card", kwargs={
                    "user_id": self.user.id,
                    "pk": self.card_1.id
                }))

        self.assertEqual(response_all_cards.json()["count"], 1)
        self.assertDictEqual(response_card_1.json(),
                             response_all_cards.json()["results"][0])
        self.assertEqual(response_all_cards.json()["results"][0]["id"],
                         str(self.card_1.id))

    def test_single_subcategory_selected_queued_cards(self):
        self.user.selected_categories.set([self.first_sub_category])
        self.user.save()
        # additional card attached to the root category
        card = self.make_fake_cards(1)[0]
        card.categories.add(self.parent)
        card.save()
        response_all_cards = self.client.get(
            reverse_queued_cards(self.user.id))
        response_card_1 = self.client.get(
            reverse("queued_card", kwargs={
                "user_id": self.user.id,
                "pk": self.card_1.id
            }))

        self.assertDictEqual(response_card_1.json(),
                             response_all_cards.json()["results"][0])
        self.assertEqual(response_all_cards.json()["count"], 1)
        self.assertEqual(response_all_cards.json()["results"][0]["id"],
                         str(self.card_1.id))

    def test_two_sibling_categories_selected_memorized_cards(self):
        self.memorize_cards()
        self.user.selected_categories.set([self.second_sub_category,
                                           self.third_sub_category])
        self.user.save()
        response_all_cards = self.client.get(
            reverse_memorized_cards(self.user.id))

        self.assertEqual(response_all_cards.json()["count"], 2)

    def test_two_sibling_categories_selected_outstanding_cards(self):
        self.memorize_cards()
        self.user.selected_categories.set([self.second_sub_category,
                                           self.third_sub_category])
        self.user.save()
        travel_time = datetime.today() + timedelta(days=4)
        with time_machine.travel(travel_time):
            response_all_cards = self.client.get(
                reverse_memorized_cards(self.user.id))

        self.assertEqual(response_all_cards.json()["count"], 2)

    def test_two_sibling_categories_selected_queued_cards(self):
        self.user.selected_categories.set([self.second_sub_category,
                                           self.third_sub_category])
        self.user.save()
        response_all_cards = self.client.get(
            reverse_queued_cards(self.user.id))

        self.assertEqual(response_all_cards.json()["count"], 2)


class CategoryTree(ApiTestHelpersMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.top_level_category = Category(name="Toplevel")
        self.top_level_category.save()
        self.sub_category = Category(name="Top-level's subcategory",
                                     parent=self.top_level_category)
        self.sub_category.save()
        self.sibling_2nd_level_category = Category(
            name="Top-level subcategory's sibling",
            parent=self.top_level_category)
        self.sibling_2nd_level_category.save()
        self.sub_sub_category = Category(name="Sub-category's subcategory",
                                         parent=self.sub_category)
        self.sub_sub_category.save()
        (self.card_top_level, self.card_sub_category,
         self.card_sibling_category,
         self.card_lowest_category) = self.cards = self.make_fake_cards(4)

        self.card_top_level.categories.add(self.top_level_category)
        self.card_sub_category.categories.add(self.sub_category)
        self.card_lowest_category.categories.add(self.sub_sub_category)
        # card in two categories
        self.card_sibling_category.categories.set([
            self.sub_category,
            self.sibling_2nd_level_category])

    def memorize_cards(self):
        for card in self.cards:
            card.memorize(self.user)

    def test_middle_category_is_selected_memorized_cards(self):
        self.memorize_cards()
        self.user.selected_categories.add(self.sub_category)
        self.user.save()
        response = self.client.get(reverse_memorized_cards(self.user.id))
        card_ids_from_response = {
            card["id"] for card in response.json()["results"]
        }
        card_ids = {
            str(card.id) for card in (self.card_sub_category,
                                      self.card_lowest_category,
                                      self.card_sibling_category)
        }

        self.assertEqual(response.json()["count"], 3)
        self.assertEqual(card_ids_from_response, card_ids)

    def test_middle_category_is_selected_queued_cards(self):
        self.user.selected_categories.add(self.sub_category)
        self.user.save()
        response = self.client.get(reverse_queued_cards(self.user.id))
        card_ids_from_response = {
            card["id"] for card in response.json()["results"]
        }
        card_ids = {
            str(card.id) for card in (self.card_sub_category,
                                      self.card_lowest_category,
                                      self.card_sibling_category)
        }

        self.assertEqual(response.json()["count"], 3)
        self.assertEqual(card_ids_from_response, card_ids)

    def test_lowest_level_category_is_selected_memorized_cards(self):
        self.memorize_cards()
        self.user.selected_categories.add(self.sub_sub_category)
        self.user.save()
        response = self.client.get(reverse_memorized_cards(self.user.id))
        card_id = response.json()["results"][0]["id"]

        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(str(self.card_lowest_category.id), card_id)

    def test_lowest_level_category_is_selected_queued_cards(self):
        self.user.selected_categories.add(self.sub_sub_category)
        self.user.save()
        response = self.client.get(reverse_queued_cards(self.user.id))
        card_id = response.json()["results"][0]["id"]

        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(str(self.card_lowest_category.id), card_id)

    def test_card_in_two_categories_memorized_cards(self):
        """Test adding card into two categories.
        """
        self.memorize_cards()
        self.user.selected_categories.add(self.sibling_2nd_level_category)
        self.user.save()
        response = self.client.get(reverse_memorized_cards(self.user.id))
        card_id = response.json()["results"][0]["id"]

        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(str(self.card_sibling_category.id), card_id)

    def test_card_in_two_categories_queued_cards(self):
        """Test adding card into two categories.
        """
        self.user.selected_categories.add(self.sibling_2nd_level_category)
        self.user.save()
        response = self.client.get(reverse_queued_cards(self.user.id))
        card_id = response.json()["results"][0]["id"]

        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(str(self.card_sibling_category.id), card_id)


class CategoryApi(ApiTestHelpersMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.top_category = Category.objects.create(name="Top level category")
        self.sub_category = Category.objects.create(name="Sub-category",
                                                    parent=self.top_category)
        self.sub_sub_category = Category.objects.create(
            name="Sub-sub-category",
            parent=self.sub_category)

    def send_selected_categories(self, categories_ids, client=None):
        local_client = client or self.client
        return local_client.put(
            reverse_selected_categories(self.user.id),
            categories_ids,
            format="json"
            # content_type="application/json"
        )

    def select_category(self):
        self.user.selected_categories.add(self.sub_sub_category)
        self.user.save()

    def get_categories_ids(self):
        return {
            str(category.id) for category in (self.top_category,
                                              self.sub_category,
                                              self.sub_sub_category)
        }

    def test_getting_user_categories_selected(self):
        """Test getting selected categories within endpoint's output.
        """
        self.user.selected_categories.add(self.sub_sub_category)
        response = self.client.get(
            reverse("user_categories", kwargs={"user_id": self.user.id}))
        response_body = response.json()
        selected_categories = response_body.get("selected_categories", None)
        expected = [str(self.sub_sub_category.id)]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(selected_categories)
        self.assertEqual(len(selected_categories), 1)
        self.assertEqual(selected_categories, expected)

    def test_getting_user_categories(self):
        """Test the 'categories' tree key from the endpoint.
        """
        self.user.selected_categories.add(self.sub_sub_category)
        response = self.client.get(
            reverse("user_categories", kwargs={"user_id": self.user.id}))
        response_body = response.json()
        categories = response_body.get("categories", None)
        expected_category_tree = {
            "key": str(self.top_category.id),
            "title": self.top_category.name,
            "children": [
                {
                    "key": str(self.sub_category.id),
                    "title": self.sub_category.name,
                    "children": [
                        {
                            "key": str(self.sub_sub_category.id),
                            "title": self.sub_sub_category.name,
                            "children": []
                        }
                    ]
                }
            ]
        }

        self.assertTrue(categories)
        self.assertEqual(len(response_body), 2)
        self.assertEqual(len(categories), 1)
        self.assertDictEqual(expected_category_tree, categories[0])

    def test_other_user_id(self):
        """Attempt to download categories using other user's id in the URL.
        """
        user = get_user_model()(username=fake.name(),
                                email=fake.email())
        response = self.client.get(
            reverse("user_categories", kwargs={"user_id": user.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthorized(self):
        """Unauthorized attempt to download (user) categories.
        """
        client = APIClient()
        response = client.get(
            reverse("user_categories", kwargs={"user_id": self.user.id}))
        expected_message = {
            # "status_code": status.HTTP_403_FORBIDDEN,
            "detail": "Authentication credentials were not provided."
        }

        self.assertDictEqual(expected_message, response.json())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieving_selected_user_categories_forbidden(self):
        """Attempt by unauthorized user to download other user's selected
        categories.
        """
        self.select_category()
        client = APIClient()
        response = client.get(reverse_selected_categories(self.user.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieving_selected_user_categories_wrong_id(self):
        """Attempt to download selected user categories using another user's
        id in the URL.
        """
        self.select_category()
        user = self.make_fake_users(1)[0]
        response = self.client.get(reverse_selected_categories(user.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieving_selected_user_categories(self):
        self.select_category()
        response = self.client.get(reverse_selected_categories(self.user.id))
        response_body = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_body), 1)
        self.assertEqual(response_body[0], str(self.sub_sub_category.id))

    def test_saving_selected_categories_forbidden(self):
        """Attempt to save selected categories from an unauthorized user.
        """
        client = APIClient()
        categories_ids = self.get_categories_ids()
        response = self.send_selected_categories(list(categories_ids),
                                                 client=client)
        response_body = response.json()

        # self.assertEqual(response_body["status_code"], "403")
        self.assertEqual(response_body["detail"],
                         "Authentication credentials were not provided.")
        self.assertTrue(status.is_client_error(response.status_code))

    def test_saving_selected_categories_wrong_user_id(self):
        """Attempt to save selected categories using other user's id
        in the URL.
        """
        categories_ids = self.get_categories_ids()
        user = self.make_fake_users(1)[0]
        response = self.client.put(
            reverse_selected_categories(user.id),
            json.dumps(list(categories_ids)), format="json"
        )
        response_body = response.json()

        self.assertTrue(status.is_client_error(response.status_code))
        self.assertEqual(response_body["detail"],
                         "You do not have permission to perform this action.")
        self.assertEqual(response_body["status_code"],
                         str(status.HTTP_403_FORBIDDEN))

    def test_saving_selected_categories_malformed_data(self):
        keys_amount = 3
        categories_ids = [fake.text(10) for _ in range(keys_amount)]
        response = self.send_selected_categories(categories_ids)
        response_detail = response.json()["detail"]

        self.assertEqual(response_detail, "Malformed data: invalid UUIDs.")
        self.assertTrue((status.is_client_error(response.status_code)))

    def test_saving_selected_categories_fake_ids(self):
        """Test fake category keys uploaded to the server.
        """
        keys_amount = 3
        categories_ids = [str(uuid.uuid4()) for _ in range(keys_amount)]
        response = self.send_selected_categories(categories_ids)
        response_detail = response.json()["detail"]

        self.assertTrue(status.is_client_error(response.status_code))
        self.assertEqual(response_detail, "Invalid input: one or more"
                                          " categories was not found.")

    def test_saving_selected_categories_malformed_body(self):
        """Test saving malformed request body to the server: text/plain
        instead of text/json.
        """
        malformed_data = fake.text(50)
        response = self.client.put(
            reverse_selected_categories(self.user.id),
            malformed_data,
            content_type="application/x-www-form-urlencoded"
        )
        self.assertTrue(status.is_client_error(response.status_code))

    def test_saving_selected_categories(self):
        categories_ids = self.get_categories_ids()
        response = self.send_selected_categories(list(categories_ids))
        selected_categories_id = {
            str(category.id) for category
            in self.user.selected_categories.all()
        }

        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(categories_ids, selected_categories_id)


class Statistics(ApiTestFakeUsersCardsMixin, TestCase):
    """Test responses to requests send to
    /api/users/{user_id}/cards/distribution
    """
    def setUp(self):
        ApiTestFakeUsersCardsMixin.setUp(self)
        self.selected_category = Category.objects.create(
            name="user selected category")
        self.user.selected_categories.set([self.selected_category])
        self.user.save()

    def test_memorization_distribution(self):
        """Test request for memorization rate - cards memorized
        on a particular date.
        """
        days_range = -4
        timedelta_days = -1
        expected_response = {}
        number_of_cards = 5

        for card in self.make_fake_cards(number_of_cards):
            if timedelta_days < days_range:
                timedelta_days = -1
            card.categories.set([self.selected_category])
            introduction_date = date.today() + timedelta(timedelta_days)
            with time_machine.travel(introduction_date):
                card.memorize(self.user)
            timedelta_days -= 1
            if expected_response.get(str(introduction_date)):
                expected_response[str(introduction_date)] += 1
            else:
                expected_response[str(introduction_date)] = 1

        url = (reverse("distribution_dynamic_part", kwargs={
            "user_id": self.user.id,
            "dynamic_part": "memorized"})
            + f"?days-range={abs(days_range)}")

        response = self.client.get(url)
        received_data = response.json()
        self.assertDictEqual(expected_response, received_data)

    def test_memorization_distribution_limit_exceeded(self):
        days_range = 40  # more than MAX_LIMIT = 31
        url = (reverse("distribution_dynamic_part", kwargs={
            "user_id": self.user.id,
            "dynamic_part": "memorized"})
               + f"?days-range={days_range}")
        response = self.client.get(url)
        received_data = response.json()
        expected_data = {
            "detail": "Allowed days range is set to 31 days."
        }

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(received_data, expected_data)

    def test_memorization_distribution_float_in_query(self):
        """Should fail: floating point number as days-range argument.
        """
        url = reverse("distribution_dynamic_part", kwargs={
            "user_id": self.user.id,
            "dynamic_part": "memorized"}) + "?days-range=1.5"
        response = self.client.get(url)
        received_data = response.json()
        expected_data = {
            "detail": "days-range must be a positive number"
        }

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(received_data, expected_data)

    def test_memorization_distribution_negative_in_query(self):
        """Should fail: negative number as days-range argument.
        """
        url = reverse("distribution_dynamic_part", kwargs={
            "user_id": self.user.id,
            "dynamic_part": "memorized"}) + "?days-range=-3"
        response = self.client.get(url)
        received_data = response.json()
        expected_data = {
            "detail": "days-range must be a positive number"
        }

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(received_data, expected_data)

    def test_memorization_distribution_string_in_query(self):
        """Should fail: string as days-range argument.
        """
        url = (reverse("distribution_dynamic_part", kwargs={
            "user_id": self.user.id,
            "dynamic_part": "memorized"})
               + "?days-range=seven+days")
        response = self.client.get(url)
        received_data = response.json()
        expected_data = {
            "detail": "days-range must be a positive number"
        }

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(received_data, expected_data)

    def test_cards_distribution_days(self):
        """Test response to request for cards distribution (number of
        reviews in the following days).
        """
        days_range = 4
        timedelta_days = 1
        expected_response = {}
        number_of_cards = 5

        for card in self.make_fake_cards(number_of_cards):
            if timedelta_days > days_range:
                timedelta_days = 1
            card.categories.set([self.selected_category])
            memorized_card = card.memorize(self.user)
            review_date = date.today() + timedelta(timedelta_days)
            memorized_card.review_date = review_date
            memorized_card.save()
            timedelta_days += 1
            if expected_response.get(str(review_date)):
                expected_response[str(review_date)] += 1
            else:
                expected_response[str(review_date)] = 1

        url = self.cards_distribution_url(days_range)
        response = self.client.get(url)
        received_data = response.json()

        self.assertDictEqual(expected_response, received_data)

    def test_cards_with_categories_distribution(self):
        days_range = 4
        distribution_range = 3
        number_of_cards = 5
        cards_selected_category_number = ceil(number_of_cards/2)
        cards = [card.memorize(self.user) for card in
                 self.make_fake_cards(number_of_cards)]
        self.unselected_category = Category.objects.create(
            name="not selected category")
        for card in cards[:cards_selected_category_number]:
            card.card.categories.set([self.selected_category])
            card.card.save()
        for card in cards[cards_selected_category_number:]:
            card.card.categories.set([self.unselected_category])
            card.card.save()

        expected_output = {
            str(date.today() + timedelta(days)):
                1 if days <= distribution_range else 0
            for days in range(1, days_range+1)
        }
        url = self.cards_distribution_url(days_range)
        response = self.client.get(url)
        received_data = response.json()

        self.assertDictEqual(expected_output, received_data)

    def test_cards_distribution_limit_exceeded(self):
        """Should fail: attempt to get cards distribution beyond allowed
        limit.
        """
        days_range = 40  # more than MAX_LIMIT = 31
        url = self.cards_distribution_url(days_range)
        response = self.client.get(url)
        received_data = response.json()
        expected_data = {
            "detail": "Allowed days range is set to 31 days."
        }

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(received_data, expected_data)

    def test_cards_distribution_malformed_query_floating_number(self):
        """Should fail: attempt to dispatch malformed url:
        floating point number as an argument for 'days_range'.
        """
        days_range = 1.5
        url = self.cards_distribution_url(days_range)
        response = self.client.get(url)
        received_data = response.json()
        expected_data = {
            "detail": "days-range must be a positive number"
        }

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(received_data, expected_data)

    def test_cards_distribution_malformed_query_negative_number(self):
        """Should fail: attempt to dispatch malformed url:
        negative number as an argument for 'days_range'.
        """
        days_range = -7
        url = self.cards_distribution_url(days_range)
        response = self.client.get(url)
        received_data = response.json()
        expected_data = {
            "detail": "days-range must be a positive number"
        }

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(received_data, expected_data)

    def test_cards_distribution_malformed_query_string(self):
        """Should fail: attempt to dispatch malformed url:
        string as an argument for 'days_range'.
        """
        days_range = "seven+days"
        url = self.cards_distribution_url(days_range)
        response = self.client.get(url)
        received_data = response.json()
        expected_data = {
            "detail": "days-range must be a positive number"
        }

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(received_data, expected_data)

    def test_grades_distribution(self):
        cards = self.make_fake_cards(10)
        self.client.force_authenticate(user=self.user)
        grades_distribution = {str(grade): 0 for grade in range(0, 6)}

        for card in cards:
            grade = randint(0, 5)
            grades_distribution[str(grade)] += 1
            card.memorize(self.user, grade)

        url = reverse("distribution_dynamic_part", kwargs={
            "user_id": self.user.id,
            "dynamic_part": "grades"})
        response = self.client.get(url)
        response_data = response.json()

        self.assertDictEqual(grades_distribution, response_data)

    def test_e_factor_distribution(self):
        cards = self.make_fake_cards(10)
        distribution = []
        e_factors = {}
        for i in range(len(cards)):
            grade = i if i <= 5 else randint(0, 5)
            memorized_card = cards[i].memorize(self.user, grade)
            e_factor = memorized_card.easiness_factor
            e_factors[e_factor] = str(
                round(memorized_card.easiness_factor, 2))

        for e_factor in sorted(e_factors.keys()):
            distribution.append({
                "e-factor": e_factors[e_factor],
                "count": CardUserData.objects.filter(
                    user=self.user,
                    easiness_factor=e_factor).count()
            })

        url = reverse("distribution_dynamic_part", kwargs={
            "user_id": self.user.id,
            "dynamic_part": "e-factor"})
        response = self.client.get(url)
        response_data = response.json()

        self.assertCountEqual(distribution, response_data)

    def cards_distribution_url(self, days_range):
        url = reverse("distribution", kwargs={
            "user_id": self.user.id}) + f"?days-range={days_range}"
        return url
