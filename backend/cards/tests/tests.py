from datetime import timedelta, date, datetime
from hashlib import sha1
from random import randint
from unittest import skip

import django.db.utils
import time_machine
from django.core.files import File
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.test import TestCase
from django.urls import reverse
from cards.models import (Card, CardUserData, Image, Sound)
from django.core.files.uploadedfile import SimpleUploadedFile
from cards.utils.exceptions import CardReviewDataExists, ReviewBeforeDue
from cards.utils.helpers import today
from cards.tests.fake_data import fake, fake_data_objects, Helpers
import datetime

make_fake_cards = fake_data_objects.make_fake_cards

class FakeUsersCards(TestCase):
    # TODO: Delete this whole class !!!
    user_model = get_user_model()

    def setUp(self):
        self.add_fake_users()
        self.add_fake_cards()

    def get_cards(self):
        """Returns three example cards.
        """
        card_1 = Card.objects.get(front=self.cards_data["first"]["front"])
        card_2 = Card.objects.get(front=self.cards_data["second"]["front"])
        card_3 = Card.objects.get(front=self.cards_data["third"]["front"])
        return card_1, card_2, card_3

    @classmethod
    def get_users(cls):
        """Returns two example users.
        """
        user_1 = cls.user_model.objects.get(username="first_user")
        user_2 = cls.user_model.objects.get(username="second_user")
        return user_1, user_2

    @classmethod
    def add_fake_users(cls):
        user_1 = cls.user_model(username="first_user")
        user_2 = cls.user_model(username="second_user")
        user_1.save()
        user_2.save()

    def add_fake_cards(self):
        self.cards_data = {
            "first": self.fake_card_data(),
            "second": self.fake_card_data(),
            "third": self.fake_card_data()
        }
        for key in self.cards_data:
            Card(**self.cards_data[key]).save()

    @staticmethod
    def fake_card_data():
        fake_text_len = (30, 100,)
        return {
            "front": fake.text(randint(*fake_text_len)),
            "back": fake.text(randint(*fake_text_len))
        }

    def get_card_user(self):
        card, *_ = self.get_cards()
        user, _ = self.get_users()
        return card, user


class CardReviewsTests(FakeUsersCards, Helpers):
    def test_no_user_foreign_keys_in_join_table(self):
        card, *_ = self.get_cards()
        self.assertRaises(django.db.utils.IntegrityError,
                          lambda: self.raise_error(
                              CardUserData.objects.create(card=card).save))

    def test_no_card_foreign_key_in_join_table(self):
        user, _ = self.get_users()
        self.assertRaises(django.db.utils.IntegrityError,
                          lambda: self.raise_error(
                              CardUserData.objects.create(user=user).save))

    @staticmethod
    def raise_error(failing_transaction):
        """The reason for adding this method is explained here:
        TransactionManagementError "You can't execute queries until
        the end of the 'atomic' block" while using signals, but only during
        Unit Testing
        https://stackoverflow.com/questions/21458387/ ...
        """
        with transaction.atomic():
            failing_transaction()

    def test_uniqueness(self):
        card, user = self.get_card_user()
        CardUserData(card=card, user=user).save()

        self.assertRaises(django.db.utils.IntegrityError,
                          CardUserData(card=card, user=user).save)

    def test_updating_review_data(self):
        """Updating card’s comment field doesn’t affect other fields.
        """
        card = make_fake_cards(1)[0]
        user, _ = self.get_users()
        card_user_data = card.memorize(user)
        card_user_data_dict = {
            "reviews": card_user_data.reviews,
            "total_reviews": card_user_data.total_reviews,
            "introduced_on": card_user_data.introduced_on,
            "review_date": card_user_data.review_date,
            "last_reviewed": card_user_data.last_reviewed,
            "grade": card_user_data.grade,
            "easiness_factor": card_user_data.easiness_factor
        }
        with time_machine.travel(date.today() + timedelta(days=10)):
            card_user_data.comment = "comment"
            card_user_data.save()

        card_user_data.refresh_from_db()
        card_user_data_output = {
            "reviews": card_user_data.reviews,
            "total_reviews": card_user_data.total_reviews,
            "introduced_on": card_user_data.introduced_on,
            "review_date": card_user_data.review_date,
            "last_reviewed": card_user_data.last_reviewed,
            "grade": card_user_data.grade,
            "easiness_factor": card_user_data.easiness_factor
        }

        self.assertDictEqual(card_user_data_dict, card_user_data_output)

    def test_backrefs(self):
        card, *_ = self.get_cards()
        user1, user2 = self.get_users()
        CardUserData(card=card, user=user1).save()
        CardUserData(card=card, user=user2).save()

        self.assertEqual(card.reviewing_users.get(id=user1.id).username,
                         user1.username)
        self.assertEqual(user2.memorized_cards.get(id=card.id).front,
                         card.front)
        self.assertEqual(card.reviewing_users.count(), 2)
        self.assertEqual(user1.memorized_cards.count(), 1)
        self.assertEqual(user1.memorized_cards.first().front,
                         card.front)

    def test_deleting_reviews_data(self):
        card, *_ = self.get_cards()
        user1, user2 = self.get_users()
        CardUserData(card=card, user=user1).save()
        CardUserData.objects.get(card=card, user=user1).delete()

        self.assertTrue(all([user1.id, card.id]))
        self.assertEqual(CardUserData.objects.count(), 0)

    def test_deleting_users_cards(self):
        card, user = self.get_card_user()
        CardUserData(card=card, user=user).save()
        user.delete()

        self.assertFalse(CardUserData.objects.first())
        self.assertTrue(card.id)

    def test_introduced_on_field(self):
        review_data = self.get_review_data()
        review_data.save()

        self.assertTrue(type(review_data.introduced_on) is datetime.datetime)
        self.assertEqual(review_data.introduced_on.date(), today())

    def test_last_reviewed_default(self):
        card, user = self.get_card_user()
        CardUserData(card=card, user=user).save()

        # the field shall be updated on introduction and on each review
        self.assertEqual(CardUserData.objects.first().last_reviewed,
                         today())

    def test_last_computed_interval_default(self):
        review_data = self.get_review_data()
        self.assertEqual(review_data.computed_interval, 0)

    def test_current_real_interval_default(self):
        review_data = self.get_review_data()
        self.assertEqual(review_data.current_real_interval, 0)

    def test_review_date_default(self):
        review_data = self.get_review_data()
        self.assertEqual(review_data.review_date, today())

    def test_review_date_is_nullable(self):
        # looks like Django's db fields are non-nullable by default
        review_data = self.get_review_data()
        review_data.review_date = None

        self.assertRaises(django.db.utils.IntegrityError, review_data.save)

    def test_repetitions_default(self):
        review_data = self.get_review_data()
        self.assertEqual(review_data.reviews, 1)

    def test_default_grade(self):
        review_data = self.get_review_data()
        default_grade = 4

        self.assertEqual(review_data.grade, default_grade)

    def get_review_data(self):
        card, user = self.get_card_user()
        review_data = CardUserData(card=card, user=user)
        return review_data

    def test_memorize_card(self):
        card, user = self.get_card_user()
        grade = 4
        easiness_factor = 2.5
        review_data_from_return = card.memorize(user, grade=grade)
        review_data = CardUserData.objects.get(card=card, user=user)

        self.assertEqual(review_data_from_return, review_data)
        self.assertEqual(review_data.reviews, 1)
        self.assertEqual(review_data.review_date,
                         date.today() + timedelta(days=1))
        self.assertEqual(review_data.grade, grade)
        self.assertEqual(review_data.easiness_factor, easiness_factor)

    def test_already_memorized(self):
        """Expected behaviour for attempt to once again memorize already
        memorized card.
        """
        card, user = self.get_card_user()
        card.memorize(user)

        # subsequent calls to Card.memorize() shall raise exception
        self.assertRaises(CardReviewDataExists, lambda: card.memorize(user))

    def test_first_review(self):
        """Test for initial card review (card memorization).
        """
        card, user = self.get_card_user()
        first_review = card.memorize(user, grade=4)
        first_review_obtained_data = {
            "easiness": first_review.easiness_factor,
            "last_reviewed": first_review.last_reviewed,
            "last_comp_interval": first_review.computed_interval,
            "current_real_interval": first_review.current_real_interval,
            "repetitions": first_review.reviews,
            "next_review": first_review.review_date
        }
        first_review_expected_data = {
            "easiness": 2.5,
            "last_reviewed": today(),
            "last_comp_interval": 1,
            "current_real_interval": 0,
            "repetitions": 1,
            "next_review": today() + timedelta(1)
        }

        self.assertDictEqual(first_review_obtained_data,
                             first_review_expected_data)

    def test_second_review(self):
        """Test for 2nd review, since it is calculated differently than
        1st and any subsequent.
        """
        days_delta = 7
        destination_date = datetime.date.today() + timedelta(days_delta)
        card, user = self.get_card_user()
        first_review_grade = 4
        # with grade < 4 card is added to cram
        second_review_grade = 3
        first_review = card.memorize(user, grade=first_review_grade)

        with time_machine.travel(destination_date):
            self.assertEqual(first_review.current_real_interval,
                             days_delta)

            second_review = card.review(user=user, grade=second_review_grade)
            second_review_obtained_data = {
                "introduced_on": second_review.introduced_on.date(),
                "easiness": second_review.easiness_factor,
                "last_reviewed": second_review.last_reviewed,
                "grade": second_review.grade,
                "last_comp_interval": second_review.computed_interval,
                "repetitions": second_review.reviews,
                "next_review": second_review.review_date,
                "crammed": second_review.crammed
            }
            second_review_expected_data = {
                "introduced_on": today() - timedelta(days_delta),
                "easiness": 2.36,
                "last_reviewed": date.today(),
                "grade": 3,
                "last_comp_interval": 6,
                "repetitions": 2,
                "next_review": (today() + timedelta(6)),
                "crammed": True
            }

        self.assertDictEqual(second_review_obtained_data,
                             second_review_expected_data)

    def test_subsequent_reviews(self):
        card, user = self.get_card_user()
        grades = (3, 4, 5, 3, 2, 4,)
        expected_comp_intervals = (6, 38, 119, 300, 1, 1,)

        review = card.memorize(user=user, grade=4)
        next_review_date = review.review_date
        i = 0
        for grade in grades:
            with time_machine.travel(next_review_date):
                review_data = card.review(
                    user=user, grade=grade)
                next_review_date = (review_data.review_date
                                    + timedelta(days=10))
                self.assertEqual(expected_comp_intervals[i],
                                 review_data.computed_interval)
            i += 1

    def test_card_forgetting_success(self):
        card, user = self.get_card_user()
        card.memorize(user, grade=4)
        card.forget(user)

        self.assertRaises(
            ObjectDoesNotExist,
            lambda: CardUserData.objects.get(user=user, card=card))

    def test_forgetting_non_existent_relationship(self):
        """Attempt to forget (remove from the learning process)
        non-existent card/user combination.
        """
        user_1, user_2 = self.get_users()
        card, *_ = self.get_cards()
        card.memorize(user_1)

        self.assertRaises(ObjectDoesNotExist, lambda: card.forget(user_2))

    @skip("Needs update")
    def test_ReviewDataSM2_serialization(self):
        card, user = self.get_card_user()
        card.memorize(user)
        review_data = CardUserData.objects.get(user=user, card=card)
        expected_rdsm2_serialization = \
            f"CardUserData(user='{str(user)}' card='{str(card)}')"

        self.assertEqual(expected_rdsm2_serialization,
                         str(review_data))

    def test_selecting_optimal_date_after_memorizing(self):
        cards_number = 7
        user, _ = self.get_users()
        cards = [Card(**self.fake_card_data()) for i in range(cards_number)]
        for card in cards:
            card.save()
            card.memorize(user)

        first_day = CardUserData.objects.filter(
            review_date=date.today() + timedelta(1)).count()
        second_day = CardUserData.objects.filter(
            review_date=date.today() + timedelta(2)).count()
        third_day = CardUserData.objects.filter(
            review_date=date.today() + timedelta(3)).count()
        fourth_day = CardUserData.objects.filter(
            review_date=date.today() + timedelta(4)).count()

        # numbers won't be valid if distribution range != 3
        self.assertEqual(first_day, 3)
        self.assertEqual(second_day, 2)
        self.assertEqual(third_day, 2)
        self.assertEqual(fourth_day, 0)

    def test_selecting_optimal_date_card_review(self):
        cards_number = 10
        user, _ = self.get_users()
        cards = [Card(**self.fake_card_data()) for i in range(cards_number)]
        reviews_number = 3

        for card in cards:
            card.save()
            review_date = card.memorize(user).review_date
            for i in range(reviews_number):
                with time_machine.travel(review_date):
                    review_date = card.review(user, 5).review_date

        reviews_last_day = CardUserData.objects.filter(
            user=user,
            review_date=review_date).count()
        self.assertLess(reviews_last_day, cards_number)
        self.assertGreater(reviews_last_day, 0)

    def test_invalid_grades_to_memorize(self):
        card, user = self.get_card_user()

        self.assertRaises(ValueError, lambda: card.memorize(user, grade=6))
        self.assertRaises(ValueError, lambda: card.memorize(user, grade=-1))
        self.assertRaises(ValueError, lambda: card.memorize(user, grade=3.5))

    def test_invalid_grades_to_review(self):
        card, user = self.get_card_user()
        card.memorize(user)

        self.assertRaises(ValueError, lambda: card.review(user, 6))
        self.assertRaises(ValueError, lambda: card.review(user, -1))
        self.assertRaises(ValueError, lambda: card.review(user, 3.5))

    def test_intervals_simulation_before_memorization(self):
        card, user = self.get_card_user()
        review_date = datetime.date.today() + datetime.timedelta(days=1)
        expected_output = {
            0: dict(
                easiness=1.7000000000000002, interval=1, reviews=0,
                review_date=review_date
            ),
            1: dict(
                easiness=1.96, interval=1, reviews=0,
                review_date=review_date
            ),
            2: dict(
                easiness=2.1799999999999997, interval=1, reviews=0,
                review_date=review_date
            ),
            3: dict(
                easiness=2.36, interval=1, reviews=1,
                review_date=review_date
            ),
            4: dict(
                easiness=2.5, interval=1, reviews=1,
                review_date=review_date
            ),
            5: dict(
                easiness=2.6, interval=1, reviews=1,
                review_date=review_date
            )
        }
        simulation = card.simulate_reviews(user)

        self.assertDictEqual(expected_output, simulation)

    def test_intervals_simulation_before_second_review(self):
        card, user = self.get_card_user()
        card.memorize(user, grade=4)
        next_review_failed = datetime.date.today() + timedelta(days=1)
        next_review_success = datetime.date.today() + timedelta(days=6)
        simulation = card.simulate_reviews(user)
        expected_output = {
            0: {'easiness': 1.7000000000000002, 'interval': 1,
                'reviews': 0, 'review_date': next_review_failed},
            1: {'easiness': 1.96, 'interval': 1, 'reviews': 0,
                'review_date': next_review_failed},
            2: {'easiness': 2.1799999999999997, 'interval': 1,
                'reviews': 0, 'review_date': next_review_failed},
            3: {'easiness': 2.36, 'interval': 6, 'reviews': 2,
                'review_date': next_review_success},
            4: {'easiness': 2.5, 'interval': 6, 'reviews': 2,
                'review_date': next_review_success},
            5: {'easiness': 2.6, 'interval': 6, 'reviews': 2,
                'review_date': next_review_success}
        }

        self.assertDictEqual(expected_output, simulation)

    def test_intervals_simulation_after_subsequent_review(self):
        number_of_reviews = 4
        card, user = self.get_card_user()
        review_date = card.memorize(user, grade=4).review_date
        grade = 3

        for _ in range(number_of_reviews):
            with time_machine.travel(review_date):
                review = card.review(user, grade=grade)
                review_date = review.review_date
        with time_machine.travel(review_date):
            simulation = card.simulate_reviews(user)
        next_review_failed = review_date + timedelta(days=1)
        expected_output = {
            0: {'easiness': 1.3,
                'interval': 1,
                'reviews': 0,
                'review_date': next_review_failed},
            1: {'easiness': 1.3999999999999997,
                'interval': 1,
                'reviews': 0,
                'review_date': next_review_failed},
            2: {'easiness': 1.6199999999999997,
                'interval': 1,
                'reviews': 0,
                'review_date': next_review_failed},
            3: {'easiness': 1.7999999999999998,
                'interval': 107,
                'reviews': 6,
                'review_date': review_date + timedelta(days=107)},
            4: {'easiness': 1.9399999999999997,
                'interval': 115,
                'reviews': 6,
                'review_date': review_date + timedelta(days=115)},
            5: {'easiness': 2.0399999999999996,
                'interval': 121,
                'reviews': 6,
                'review_date': review_date + timedelta(days=121)}}

        self.assertDictEqual(expected_output, simulation)

    def test_lapses(self):
        """Test CardUserData.lapses field.
        """
        number_of_reviews = 2
        grade = 4
        card, user = self.get_card_user()
        review_data = card.memorize(user, grade)

        self.assertEqual(review_data.lapses, 0)
        for _ in range(number_of_reviews):
            with time_machine.travel(review_data.review_date):
                review_data = card.review(user, grade)

        with time_machine.travel(review_data.review_date):
            review_data = card.review(user, 1)
        self.assertEqual(review_data.lapses, 1)

    def test_total_reviews(self):
        """Test cumulative reviews counting.
        """
        card, user = self.get_card_user()

        review_data = card.memorize(user, 3)
        self.assertEqual(review_data.total_reviews, 1)

        with time_machine.travel(review_data.review_date):
            review_data = card.review(user, 3)
        self.assertEqual(review_data.total_reviews, 2)

        with time_machine.travel(review_data.review_date):
            review_data = card.review(user, 1)
        self.assertEqual(review_data.total_reviews, 3)

    def test_reviewing_before_due_date(self):
        """Attempt to review cards before it's due date should raise an error.
        """
        card, user = self.get_card_user()
        card_userdata = card.memorize(user, 5)
        with time_machine.travel(card_userdata.review_date):
            card_userdata.review(5)

        self.assertRaises(ReviewBeforeDue, lambda: card_userdata.review(5))


class CardCategories(FakeUsersCards, Helpers):
    def test_card_single_category(self):
        category_name = fake.text(20)
        card, category = self.card_with_category(category_name)

        self.assertEqual(len(card.categories.all()), 1)
        self.assertEqual(card.categories.first().name, category_name)

    def test_deleting_category_keeps_card(self):
        card, category = self.card_with_category()
        category.delete()
        self.assertTrue(card.id)

    def test_deleting_card_keeps_category(self):
        card, category = self.card_with_category()
        card.delete()
        self.assertFalse(card.id)
        self.assertTrue(category.id)

    def test_card_multiple_categories(self):
        card_1, card_2, _ = self.get_cards()
        category_names = [fake.text(20) for _ in range(4)]
        categories = [fake_data_objects.make_fake_category(name)
                      for name in category_names]
        card_1.categories.add(*categories[:2])
        card_2.categories.add(*categories[2:])
        [card.save() for card in (card_1, card_2,)]
        card_1_categories = card_1.categories.all()
        card_2_categories = card_2.categories.all()

        self.assertEqual(len(card_1_categories), 2)
        self.assertEqual(len(card_2_categories), 2)
        self.assertFalse(card_1_categories[1] in card_2_categories)
        self.assertTrue(card_1_categories[0].name in category_names[:2])
        self.assertTrue(card_2_categories[0].name in category_names[2:])
        self.assertFalse(card_2_categories[0].name in category_names[:2])

        category_from_card_1 = card_1_categories[0]
        card_1.categories.set([])
        card_1.save()
        category_from_card_1.refresh_from_db()
        self.assertTrue(category_from_card_1.id)

    def card_with_category(self, category_name=fake.text(20)):
        card, *_ = self.get_cards()
        category = fake_data_objects.make_fake_category(category_name)
        card.categories.add(category)
        card.save()
        return card, category


class AbsoluteUrls(Helpers, TestCase):
    def setUp(self):
        # this should be inherited from the ApiTestHelpersMixin
        # which currently resides in api.tests
        self.client = APIClient()
        self.user = fake_data_objects.make_fake_user()
        self.client.force_authenticate(user=self.user)
        self.card = make_fake_cards(1)[0]

    def test_card_user_data_canonical_url(self):
        card_user_data = self.card.memorize(self.user)
        canonical_url = reverse("memorized_card",
                                kwargs={"pk": self.card.id,
                                        "user_id": self.user.id})

        self.assertEqual(card_user_data.get_absolute_url(), canonical_url)


class SoundFiles(Helpers, TestCase):
    def setUp(self):
        (self.sound,
         self.audio_filename) = self.add_soundfile_to_database(
            self.placeholder_audio_files[0])

    def test_adding_audio_to_database(self):
        filename_no_extension = self.audio_filename.split(".")[0]
        file_retrieved_from_db = Sound.objects.filter(
            sound_file__contains=filename_no_extension).first()
        self.assertTrue(file_retrieved_from_db)

    def test_sound_file_hashing(self):
        sound_file = SimpleUploadedFile("audio file",
                                        self.placeholder_audio_files[0],
                                        "audio/mpeg")
        sound_file_sha1_digest = sha1(sound_file.open().read()).hexdigest()
        sound_file_instance_in_db = Sound.objects.get(
            sha1_digest=sound_file_sha1_digest)
        self.assertEqual(sound_file_sha1_digest,
                         sound_file_instance_in_db.sha1_digest)


class SoundsInCards(Helpers, TestCase):
    def setUp(self):
        self.card_1, self.card_2 = make_fake_cards(2)
        sound_entries = []
        # valid as long as .placeholder_audio_files has only two elements:
        for placeholder_audio in self.placeholder_audio_files:
            entry_in_db, name = self.add_soundfile_to_database(
                placeholder_audio)
            sound_entries.append({
                "entry": entry_in_db,
                "name": name
            })
        self.sound_entry_1 = sound_entries[0]["entry"]
        self.sound_entry_2 = sound_entries[1]["entry"]

    def test_sounds_front(self):
        """Attaching one sound to multiple cards (front).
        """
        self.card_1.front_audio = self.sound_entry_1
        self.card_2.front_audio = self.sound_entry_1
        self.card_2.back_audio = self.sound_entry_2
        self.card_1.save()
        self.card_2.save()

        self.assertEqual(self.sound_entry_1.cards_front.count(), 2)
        self.assertFalse(self.sound_entry_2.cards_front.all())

    def test_sounds_back(self):
        """Attaching one sound to multiple cards (back).
        """
        self.card_1.back_audio = self.sound_entry_1
        self.card_2.back_audio = self.sound_entry_1
        self.card_2.front_audio = self.sound_entry_1
        self.card_1.save()
        self.card_2.save()

        self.assertEqual(self.sound_entry_1.cards_back.count(), 2)
        self.assertFalse(self.sound_entry_2.cards_back.all())

    def test_related_name_front(self):
        self.card_1.front_audio = self.sound_entry_1
        self.card_2.back_audio = self.sound_entry_1
        self.card_1.save()
        self.card_2.save()

        self.assertEqual(self.sound_entry_1.cards_front.count(), 1)
        self.assertEqual(self.sound_entry_1.cards_front.first(), self.card_1)

    def test_related_name_back(self):
        self.card_1.back_audio = self.sound_entry_1
        self.card_2.front_audio = self.sound_entry_1
        self.card_1.save()
        self.card_2.save()

        self.assertEqual(self.sound_entry_1.cards_back.count(), 1)
        self.assertEqual(self.sound_entry_1.cards_back.first(), self.card_1)

    def test_removing_sound_front(self):
        """Removing sound entry attached to card's front doesn't
        delete the card.
        """
        self.card_1.back_audio = self.sound_entry_1
        card_1_front = self.card_1.front
        self.card_1.save()
        self.sound_entry_1.delete()
        card_from_db = Card.objects.filter(front=card_1_front).first()

        self.assertEqual(card_from_db.front, card_1_front)
        # check if field definition's on_delete=models.SET_NULL works:
        self.assertIsNone(card_from_db.front_audio)

    def test_removing_sound_back(self):
        """Removing sound entry attached to card's back doesn't
        delete the card.
        """
        self.card_1.back_audio = self.sound_entry_1
        card_1_back = self.card_1.back
        self.card_1.save()
        self.sound_entry_1.delete()
        card_from_db = Card.objects.filter(back=card_1_back).first()

        self.assertEqual(card_from_db.back, card_1_back)
        # check if field definition's on_delete=models.SET_NULL works:
        self.assertIsNone(card_from_db.back_audio)

    def test_removing_card_front(self):
        """Removing card doesn't delete sound entry attached
        to the card's front.
        """
        self.card_1.front_audio = self.sound_entry_1
        self.card_1.save()
        self.card_1.delete()
        self.sound_entry_1.refresh_from_db()

        self.assertTrue(self.sound_entry_1)

    def test_removing_card_back(self):
        """Removing card doesn't delete sound entry attached
        to the card's back.
        """
        self.card_1.back_audio = self.sound_entry_1
        self.card_1.save()
        self.card_1.delete()
        self.sound_entry_1.refresh_from_db()

        self.assertTrue(self.sound_entry_1)


class ImageTests(Helpers, TestCase):
    @skip
    def test_image_embedding_in_card(self):
        pass

    @skip
    def test_image_embedding_in_templates(self):
        pass

    def test_image_hash_validity(self):
        small_gif = SimpleUploadedFile(name=fake.file_name(extension="gif"),
                                       content=Helpers.gifs[0],
                                       content_type="image/gif")
        small_gif_sha1_digest = sha1(small_gif.open().read()).hexdigest()
        image_in_db = Image(image=File(small_gif))
        image_in_db.save()
        self.assertEqual(small_gif_sha1_digest, image_in_db.sha1_digest)


class CardUserDataMapping(FakeUsersCards):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User(username="user")
        cls.user.save()
        cls.card = Card(front="question", back="answer")
        cls.card.save()
        cls.card.memorize(cls.user)
        cls.review_data = CardUserData.objects.get(card=cls.card,
                                                   user=cls.user)
        cls.review_data_mapping = dict(cls.review_data)

    def test_computed_interval(self):
        self.assertEqual(self.review_data.computed_interval,
                         self.review_data["computed_interval"])

    def test_lapses(self):
        self.assertEqual(self.review_data.lapses,
                         self.review_data["lapses"])

    def test_reviews(self):
        self.assertEqual(self.review_data.reviews,
                         self.review_data["reviews"])

    def test_total_reviews(self):
        self.assertEqual(self.review_data.total_reviews,
                         self.review_data["total_reviews"])

    def test_last_reviewed(self):
        self.assertEqual(self.review_data.last_reviewed,
                         self.review_data["last_reviewed"])

    def test_introduced_on(self):
        self.assertEqual(self.review_data.introduced_on,
                         self.review_data["introduced_on"])

    def test_review_date(self):
        self.assertEqual(self.review_data.review_date,
                         self.review_data["review_date"])

    def test_grade(self):
        self.assertEqual(self.review_data.grade,
                         self.review_data["grade"])

    def test_easiness_factor(self):
        self.assertEqual(self.review_data.easiness_factor,
                         self.review_data["easiness_factor"])

    def test_crammed(self):
        self.assertEqual(self.review_data.crammed,
                         self.review_data["crammed"])

    def test_comment(self):
        self.assertEqual(self.review_data.comment,
                         self.review_data["comment"])
