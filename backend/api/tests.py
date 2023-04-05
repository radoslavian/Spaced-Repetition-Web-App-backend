import json
import uuid
from math import ceil

import time_machine
from django.test import TestCase
from datetime import date, timedelta
from datetime import datetime
from random import choice, shuffle
from cards.models import Card, CardImage, CardTemplate, Category
from faker import Faker
from rest_framework import status

if __name__ == "__main__" and __package__ is None:
    # overcoming sibling module imports problem
    # in a quick and dirty way
    from sys import path
    from os.path import dirname

    path.append(dirname(path[0]))

from django.urls import reverse
from cards.tests import FakeUsersCards, HelpersMixin

fake = Faker()


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
        self.assertEqual(response.status_code, 200)
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
        self.assertEqual(response_json["categories"][0]["name"],
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
        self.assertNotEqual(categories_from_response[0]["id"],
                            categories_from_response[1]["id"])
        self.assertNotEqual(categories_from_response[0]["name"],
                            categories_from_response[1]["name"])


class UserDataCardsTests(FakeUsersCards, HelpersMixin):
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
        response = self.get_response_for_card_with_userdata(card, user)
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
        response = self.get_response_for_card_with_userdata(card, user)
        received_card_body = response.json()["body"]

        self.assertTrue("<!-- base template for cards-->"
                        in received_card_body)
        self.assertTrue("<!-- test template -->" in received_card_body)
        self.assertTrue(card.front in received_card_body)
        self.assertTrue(card.front in received_card_body)

    def get_response_for_card_with_userdata(self, card, user):
        response = self.client.get(
            reverse("card_for_user",
                    kwargs={"card_pk": card.id, "user_pk": user.id}))
        return response

    def test_review_data(self):
        card, user = self.get_card_user()
        review_data = card.memorize(user, 5)
        response = self.get_response_for_card_with_userdata(card, user)
        introduced_on = review_data.introduced_on \
            .isoformat().replace("+00:00", "Z")
        expected_data = {
            "computed_interval": review_data.computed_interval,
            "lapses": review_data.lapses,
            "total_reviews": review_data.total_reviews,
            "last_reviewed": str(review_data.last_reviewed),
            "crammed": False,
            "introduced_on": introduced_on,
            "review_date": str(review_data.review_date),
            "grade": review_data.grade,
            "reviews": review_data.reviews,
            "categories": [],
            "easiness_factor": review_data.easiness_factor,
            "card": str(card.id)
        }
        received_data = response.json()
        received_data.pop("body")
        received_data.pop("projected_review_data")

        self.assertDictEqual(expected_data, received_data)

    def test_projected_review_data(self):
        card, user = self.get_card_user()
        card_review_data = card.memorize(user, 4)
        with time_machine.travel(card_review_data.review_date):
            six_days = str(date.today() + timedelta(days=6))
            one_day = str(date.today() + timedelta(days=1))
            response = self.get_response_for_card_with_userdata(card, user)

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
        card, user = self.get_card_user()
        card.memorize(user, 4)
        response = self.get_response_for_card_with_userdata(
            card, user)

        self.assertFalse(response.json()["projected_review_data"])

    def test_user_memorized_card_single_category(self):
        card, user = self.get_card_user()
        card.memorize(user)
        category = self.create_category()
        card.categories.add(category)
        card.save()
        response = self.get_response_for_card_with_userdata(card, user)
        categories_from_response = response.json()["categories"]
        category_name_from_response = categories_from_response[0]["name"]

        self.assertEqual(len(categories_from_response), 1)
        self.assertEqual(category_name_from_response, category.name)

    def test_user_memorized_card_two_categories(self):
        card, user = self.get_card_user()
        card.memorize(user)
        category_1 = self.create_category()
        category_2 = self.create_category()
        card.categories.add(category_1, category_2)
        card.save()
        response = self.get_response_for_card_with_userdata(card, user)
        categories_from_response = response.json()["categories"]

        self.assertEqual(len(categories_from_response), 2)
        self.assertNotEqual(categories_from_response[0],
                            categories_from_response[1])

    def test_user_not_memorized_card_single_category(self):
        card, user = self.get_card_user()
        category = self.create_category()
        card.categories.add(category)
        card.save()
        response = self.get_response_for_card_with_userdata(card, user)
        categories_from_response = response.json()["categories"]
        category_name_from_response = response.json()["categories"][0]["name"]

        self.assertEqual(len(categories_from_response), 1)
        self.assertEqual(category_name_from_response, category.name)

    def test_user_not_memorized_card_two_categories(self):
        card, user = self.get_card_user()
        category_1 = self.create_category()
        category_2 = self.create_category()
        card.categories.add(category_1, category_2)
        card.save()
        response = self.get_response_for_card_with_userdata(card, user)
        categories_from_response = response.json()["categories"]

        self.assertEqual(len(categories_from_response), 2)
        self.assertNotEqual(categories_from_response[0],
                            categories_from_response[1])


class CardMemorization(FakeUsersCards):
    def test_memorize_card_no_card(self):
        user, _ = self.get_users()
        fake_card_id = uuid.uuid4()
        response = self.client.put(
            reverse("card_for_user",
                    kwargs={"card_pk": fake_card_id, "user_pk": user.id}))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Not found.")

    def test_memorize_card_no_user(self):
        fake_user_id = uuid.uuid4()
        card, *_ = self.get_cards()
        response = self.client.put(
            reverse("card_for_user",
                    kwargs={"card_pk": card.id, "user_pk": fake_user_id}))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Not found.")

    def test_memorize_card_400(self):
        """Bad request from attempt to again memorize already memorized card.
        """
        card, user = self.get_card_user()
        card.memorize(user)
        # putting user and card to the server means card memorization:
        response = self.client.put(
            reverse("card_for_user",
                    kwargs={"card_pk": card.id, "user_pk": user.id}))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status_code"], 400)
        self.assertEqual(response.json()["detail"],
                         f"Card with id {card.id} for "
                         f"user {user.username} id ({user.id})"
                         f" is already memorized.")

    def test_memorize_success(self):
        grade = 1
        card, user = self.get_card_user()
        response = self.client.put(
            reverse("memorize_review_card",
                    kwargs={"card_pk": card.id, "user_pk": user.id,
                            "grade": grade}))

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["grade"], grade)

    def test_memorize_success_no_grade(self):
        """Successful memorization with default grade.
        """
        card, user = self.get_card_user()
        response = self.client.put(
            reverse("card_for_user",
                    kwargs={"card_pk": card.id, "user_pk": user.id}))

        self.assertEqual(response.status_code, 201)


class ReviewingCard(FakeUsersCards):
    def test_user_not_found(self):
        card, *_ = self.get_cards()
        fake_user_id = uuid.uuid4()
        response = self.client.post(
            reverse("memorize_review_card",
                    kwargs={"card_pk": card.id, "user_pk": fake_user_id,
                            "grade": 3}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["detail"], "Not found.")

    def test_card_not_found(self):
        user, *_ = self.get_users()
        fake_card_id = uuid.uuid4()
        response = self.client.post(
            reverse("memorize_review_card",
                    kwargs={"card_pk": fake_card_id, "user_pk": user.id,
                            "grade": 3}))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["detail"], "Not found.")

    def test_grade_success(self):
        card, user = self.get_card_user()
        card.memorize(user)
        response = self.client.post(
            reverse("memorize_review_card",
                    kwargs={"card_pk": card.id, "user_pk": user.id,
                            "grade": 3}))
        response_json = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_json["reviews"], 2)


class ListOfCardsForUser(TestCase, HelpersMixin):
    def test_list_of_memorized_cards(self):
        """General test for getting list of memorized cards for an app user
        (no limits, no pagination).
        """
        NUMBER_OF_CARDS = 15
        half_of_cards = ceil(NUMBER_OF_CARDS / 2)
        cards = self.make_fake_cards(NUMBER_OF_CARDS)
        user_1, user_2 = self.make_fake_users(2)
        shuffle(cards)
        memorized_cards = [card.memorize(user_1)
                           for card in cards[:half_of_cards]]
        cards[-1].memorize(user_2)
        response = self.client.get(reverse("list_of_memorized_cards_for_user",
                                           kwargs={"user_pk": user_1.id}))
        response_content = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_content["count"], half_of_cards)
        self.assertEqual(response_content["results"][0]["body"],
                         memorized_cards[0].card.body)

    def test_list_of_memorized_cards_no_user(self):
        self.make_fake_cards(2)
        fake_user_id = uuid.uuid4()
        response = self.client.get(reverse("list_of_memorized_cards_for_user",
                                           kwargs={"user_pk": fake_user_id}))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_of_not_memorized_cards_no_user(self):
        fake_user_id = uuid.uuid4()
        self.make_fake_cards(2)
        response = self.client.get(
            reverse("list_of_not_memorized_cards_for_user",
                    kwargs={"user_pk": fake_user_id}))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_of_not_memorized_cards(self):
        NUMBER_OF_CARDS = 10
        half_of_cards = ceil(NUMBER_OF_CARDS / 2)
        cards = self.make_fake_cards(NUMBER_OF_CARDS)
        user_1, user_2 = self.make_fake_users(2)
        memorized_cards = [card.memorize(user_1)
                           for card in cards[:half_of_cards]]
        not_memorized_cards = cards[half_of_cards:]
        cards[-1].memorize(user_2)
        number_of_not_memorized_cards = len(not_memorized_cards)

        response = self.client.get(
            reverse("list_of_not_memorized_cards_for_user",
                    kwargs={"user_pk": user_1.id}))
        response_body = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_body["count"],
                         number_of_not_memorized_cards)
        self.assertEqual(not_memorized_cards[0].body,
                         response_body["results"][0]["body"])

    def test_list_of_not_memorized_cards_2(self):
        NUMBER_OF_CARDS = 2
        card_1, card_2 = self.make_fake_cards(NUMBER_OF_CARDS)
        user_1, user_2 = self.make_fake_users(2)
        card_1.memorize(user_1)
        card_2.memorize(user_2)
        response = self.client.get(
            reverse("list_of_not_memorized_cards_for_user",
                    kwargs={"user_pk": user_1.id}))
        response_results = response.json()["results"]

        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(card_2.body, response_results[0]["body"])

    def test_all_cards(self):
        """Test if number of cards for both endpoints:
        for memorized and not memorized cards - equals total number of cards.
        """
        NUMBER_OF_CARDS = 100
        portion_of_cards = ceil(NUMBER_OF_CARDS / 2)
        cards = self.make_fake_cards(NUMBER_OF_CARDS)
        user_1, user_2 = self.make_fake_users(2)
        memorized_cards = [card.memorize(user_1)
                           for card in cards[:portion_of_cards]]
        response_not_memorized = self.client.get(
            reverse("list_of_not_memorized_cards_for_user",
                    kwargs={"user_pk": user_1.id}))
        response_memorized = self.client.get(
            reverse("list_of_memorized_cards_for_user",
                    kwargs={"user_pk": user_1.id}))

        # count - key from the current page (results are paginated)
        number_of_memorized_cards = response_memorized.json()["count"]
        number_of_not_memorized_cards = response_not_memorized.json()["count"]

        self.assertEqual(sum([number_of_memorized_cards,
                              number_of_not_memorized_cards]),
                         NUMBER_OF_CARDS)

    def test_outstanding_cards(self):
        """Test retrieving outstanding cards.
        """
        # should be split into two tests
        NUMBER_OF_NOT_MEMORIZED_CARDS = 2
        NUMBER_OF_MEMORIZED_CARDS = 3
        NUMBER_OF_REVIEWED_CARDS = 4
        due_for_memorized = date.today() + timedelta(days=3)
        due_for_review = due_for_memorized + timedelta(days=6)

        user = self.make_fake_users(1)[0]
        not_memorized_cards = self.make_fake_cards(
            NUMBER_OF_NOT_MEMORIZED_CARDS)
        memorized_cards = self.make_fake_cards(NUMBER_OF_MEMORIZED_CARDS)
        reviewed_cards = self.make_fake_cards(NUMBER_OF_REVIEWED_CARDS)

        for card in memorized_cards:
            card.memorize(user)

        for card in reviewed_cards:
            card_review_data = card.memorize(user)
            with time_machine.travel(card_review_data.review_date):
                card_review_data.review(4)

        with time_machine.travel(due_for_memorized):
            response_cards_memorized = self.client.get(
                reverse("outstanding_cards", kwargs={"user_pk": user.id}))

        with time_machine.travel(due_for_review):
            response_cards_for_review = self.client.get(
                reverse("outstanding_cards", kwargs={"user_pk": user.id}))
        card_for_review_body = response_cards_for_review.json()[
            "results"][0]["body"]

        self.assertEqual(response_cards_memorized.json()["count"],
                         NUMBER_OF_MEMORIZED_CARDS)
        self.assertEqual(response_cards_for_review.json()["count"],
                         NUMBER_OF_MEMORIZED_CARDS + NUMBER_OF_REVIEWED_CARDS)
        self.assertEqual(card_for_review_body, memorized_cards[0].body)

    def test_outstanding_cards_404(self):
        """Attempt to download outstanding cards using wrong user id.
        """
        fake_user_id = uuid.uuid4()
        response = self.client.get(
            reverse("outstanding_cards", kwargs={"user_pk": fake_user_id}))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CramTests(TestCase, HelpersMixin):
    def test_adding_to_cram_success(self):
        card_1, card_2 = self.make_fake_cards(2)
        user_1, user_2 = self.make_fake_users(2)
        card_1.memorize(user_1, 5)
        card_2.memorize(user_2, 5)
        response = self.client.put(
            reverse("cram_queue", kwargs={"user_pk": user_1.id,
                                          "card_pk": card_1.id}))
        response_card_body = response.json()["body"]

        self.assertTrue(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(user_1.crammed_cards), 1)
        self.assertEqual(card_1.body, response_card_body)

    def test_adding_to_cram_fail(self):
        card = self.make_fake_cards(1)[0]
        user = self.make_fake_users(1)[0]
        response = self.client.put(
            reverse("cram_queue", kwargs={"user_pk": user.id,
                                          "card_pk": card.id}))
        response_json = response.json()
        error_detail = f"The card id {card.id} is not " \
                       f"memorized by user id {user.id}."

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_json["status_code"], 400)
        self.assertEqual(response_json["detail"], error_detail)

    def test_retrieving_cram_queue(self):
        NUMBER_OF_CARDS = 20
        cards = self.make_fake_cards(NUMBER_OF_CARDS)
        user = self.make_fake_users(1)[0]
        for card in cards:
            card.memorize(user, 3)
        response = self.client.get(
            reverse("get_cram_queue", kwargs={"user_pk": user.id}))
        response_json = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_json["count"], NUMBER_OF_CARDS)

    def test_removing_card_from_cram_400(self):
        """Test response to attempt to delete not memorized card.
        """
        card = self.make_fake_cards(1)[0]
        user = self.make_fake_users(1)[0]
        response = self.client.delete(
            reverse("cram_queue", kwargs={"user_pk": user.id,
                                          "card_pk": card.id}))
        response_json = response.json()
        error_detail = f"The card id {card.id} is not " \
                       f"memorized by user id {user.id}."

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_json["status_code"], 400)
        self.assertEqual(response_json["detail"], error_detail)

    def test_removing_card_from_cram(self):
        card = self.make_fake_cards(1)[0]
        user = self.make_fake_users(1)[0]
        card.memorize(user)
        response = self.client.delete(
            reverse("cram_queue", kwargs={"user_pk": user.id,
                                          "card_pk": card.id}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)