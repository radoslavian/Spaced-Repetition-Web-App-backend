import datetime
from abc import ABC
from datetime import date, timedelta
from typing import Callable
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.utils import IntegrityError
from django.test import TestCase
import time_machine
from cards.models import CardUserData
from cards.tests.fake_data import fake, fake_data_objects
from cards.utils.exceptions import CardReviewDataExists, ReviewBeforeDue


class General(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.card = fake_data_objects.make_fake_card()
        cls.user = fake_data_objects.make_fake_user()
        cls.target_date = datetime.datetime(1985, 5, 10,
                                            0, 0, 0, 0)

        with time_machine.travel(cls.target_date):
            cls.review = cls.card.memorize(cls.user)

    def test_no_user_foreign_keys_in_join_table(self):
        """
        Should raise an error in an attempt to create a review data object
        without a user.
        """
        self.assertRaises(
            IntegrityError,
            lambda: raise_error(
                CardUserData(card=self.card).save))

    def test_no_card_foreign_key_in_join_table(self):
        """
        Should raise an error in an attempt to create a review data object
        without a card.
        """
        self.assertRaises(
            IntegrityError,
            lambda: raise_error(
                CardUserData(user=self.user).save))

    def test_review_serialization(self):
        expected_serialization = (
            'computed_interval: 1\n'
            'lapses: 0\n'
            'reviews: 1\n'
            'total_reviews: 1\n'
            'last_reviewed: 1985-05-10\n'
            f'introduced_on: {self.review.introduced_on}\n'
            'review_date: 1985-05-11\n'
            'grade: 4\n'
            'easiness_factor: 2.5\n'
            'crammed: False\n'
            'comment: None')

        self.assertEqual(expected_serialization, str(self.review))


class CardUserDataMapping(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = fake_data_objects.make_fake_user()
        cls.card = fake_data_objects.make_fake_card()
        cls.review_data = cls.card.memorize(cls.user)
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


class CramQueue(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.low_grade, cls.high_grade = 2, 5
        cls.card_1, cls.card_2, cls.card_3 = \
            fake_data_objects.make_fake_cards(3)
        cls.user = fake_data_objects.make_fake_user()

    def setUp(self):
        self.crammed_card = self.card_1.memorize(self.user, self.low_grade)
        self.not_crammed_card = self.card_2.memorize(self.user,
                                                     self.high_grade)
        self.reference_card = self.card_3.memorize(self.user, self.low_grade)
        self.reviews = [self.crammed_card, self.not_crammed_card,
                        self.reference_card]

    def tearDown(self):
        for review in self.reviews:
            review.delete()

    def test_user_crammed_cards(self):
        """
        User.crammed_cards reports number of cards in the cram queue.
        """
        expected_number_of_crammed_cards = 2

        self.assertEqual(len(self.user.crammed_cards),
                         expected_number_of_crammed_cards)

    def test_removing_crammed_card(self):
        """
        Removing a crammed card from the cram queue changes the crammed status
        of the card.
        """
        self.assertTrue(self.crammed_card.crammed)
        status = self.crammed_card.remove_from_cram()

        self.assertFalse(status)
        self.assertEqual(len(self.user.crammed_cards), 1)
        self.assertFalse(self.crammed_card.crammed)

    def test_removing_not_crammed_card(self):
        """
        An attempt to remove a card from the cram queue shouldn't change the
        status of the card.
        """
        status = self.not_crammed_card.remove_from_cram()
        self.assertFalse(status)

    def test_add_manually(self):
        """
        Manually adding a card to the cram queue.
        """
        status = self.not_crammed_card.add_to_cram()

        self.assertTrue(status)
        self.assertTrue(self.not_crammed_card.crammed)


class CardCommentCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        comment_len = 100
        cls.target_date = datetime.date(1985, 5, 10)
        cls.user = fake_data_objects.make_fake_user()
        cls.card = fake_data_objects.make_fake_card()
        cls.comment_text = fake.text(comment_len)

    def setUp(self):
        with time_machine.travel(self.target_date):
            self.card_user_data = self.card.memorize(self.user)

        self.card_user_data.comment = self.comment_text
        self.card_user_data.save()

    def tearDown(self):
        self.card_user_data.delete()

    def test_add_comment(self):
        self.assertEqual(self.card_user_data.comment, self.comment_text)

    def test_remove_comment(self):
        self.card_user_data.comment = None  # or .clear()? or = "" ?
        self.card_user_data.save()
        self.card_user_data.refresh_from_db()

        self.assertFalse(self.card_user_data.comment)

    def test_updated_comment(self):
        fake_comment = fake.text(100)
        self.card_user_data.comment = fake_comment
        self.card_user_data.save()
        self.card_user_data.refresh_from_db()

        self.assertEqual(self.card_user_data.comment, fake_comment)

    def test_updating_comment(self):
        """
        Updating card comment field doesn’t affect other fields (such as
        a review date).
        """
        comment = "user comment"
        review_in = self.clear_comment()
        travel_destination = self.target_date + timedelta(days=10)

        with time_machine.travel(travel_destination):
            self.update_comment(comment)

        review_out = self.clear_comment()

        self.assertDictEqual(review_in, review_out)

    def update_comment(self, comment):
        self.card_user_data.comment = comment
        self.card_user_data.save()

    def clear_comment(self):
        return {**self.card_user_data, "comment": None}


class MemorizeForgetCard(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.target_date = datetime.date(1985, 5, 10)
        cls.card = fake_data_objects.make_fake_card()
        cls.user = fake_data_objects.make_fake_user()

    def setUp(self):
        with time_machine.travel(self.target_date):
            self.review = self.card.memorize(self.user, grade=5)

    def tearDown(self):
        self.review.delete()

    def test_card_forgetting_success(self):
        self.card.forget(self.user)

        self.assertRaises(
            ObjectDoesNotExist,
            lambda: CardUserData.objects.get(user=self.user,
                                             card=self.card))

    def test_forgetting_non_existent_relationship(self):
        """
        An attempt to forget (remove from the learning process)
        non-existent card/user combination.
        """
        card = fake_data_objects.make_fake_card()
        self.assertRaises(ObjectDoesNotExist, lambda: card.forget(self.user))

    def test_easiness_factor(self):
        expected_easiness_factor = 2.6
        self.assertEqual(self.review.easiness_factor,
                         expected_easiness_factor)

    def test_computed_interval(self):
        expected_computed_interval = 1
        self.assertEqual(self.review.computed_interval,
                         expected_computed_interval)

    def test_last_reviewed(self):
        # self.target_date is an expected output
        self.assertEqual(self.review.last_reviewed, self.target_date)

    def test_review_date(self):
        expected_review_date = self.target_date + timedelta(days=1)
        self.assertEqual(self.review.review_date, expected_review_date)

    def test_current_real_interval(self):
        expected_current_real_interval = 0

        with time_machine.travel(self.target_date):
            self.assertEqual(self.review.current_real_interval,
                             expected_current_real_interval)

    def test_number_of_reviews(self):
        expected_number_of_reviews = 1
        self.assertEqual(self.review.reviews, expected_number_of_reviews)

    def test_grade(self):
        expected_grade = 5
        self.assertEqual(self.review.grade, expected_grade)

    def test_default_repetitions(self):
        default_repetitions = 1
        self.assertEqual(self.review.reviews, default_repetitions)

    def test_default_grade(self):
        default_grade = 4
        user = fake_data_objects.make_fake_user()
        review = self.card.memorize(user, default_grade)
        self.assertEqual(review.grade, default_grade)

    def test_memorize_return(self):
        """
        Card.memorize() should return CardUserData object instance.
        """
        review_from_db = CardUserData.objects.get(card=self.card,
                                                  user=self.user)
        self.assertIsInstance(self.review, CardUserData)
        self.assertDictEqual({**review_from_db},
                             {**self.review})

    def test_already_memorized(self):
        """
        Should raise an exception if a user attempts to memorize the same
        card again.
        """

        def re_memorize_card():
            raise_error(lambda: self.card.memorize(self.user))

        self.assertRaises(CardReviewDataExists, re_memorize_card)

    def test_uniqueness(self):
        """
        Should raise an error in an attempt to create another (identical)
        instance of CardUserData.
        """
        self.assertRaises(
            IntegrityError,
            lambda: raise_error(
                CardUserData(card=self.card, user=self.user).save))


class Backrefs(TestCase):
    @classmethod
    def setUpTestData(cls):
        grade = 5
        cls.card = fake_data_objects.make_fake_card()
        cls.user1, cls.user2 = fake_data_objects.make_fake_users(2)
        cls.card_user_data = cls.card.memorize(cls.user1, grade=grade)
        cls.reference_card_user_data = CardUserData.objects.create(
            card=cls.card,
            user=cls.user2)

    def test_reviewing_users(self):
        username_from_card = self.card.reviewing_users.get(
            id=self.user1.id).username
        self.assertEqual(username_from_card, self.user1.username)

    def test_user_memorized_card(self):
        card_from_user = self.user2.memorized_cards.get(id=self.card.id)
        user1_memorized_card_id = self.user1.memorized_cards.first().id

        self.assertEqual(card_from_user.id, self.card.id)
        self.assertEqual(user1_memorized_card_id, self.card.id)

    def test_memorized_cards_count(self):
        self.assertEqual(self.user1.memorized_cards.count(), 1)
        self.assertEqual(self.card.reviewing_users.count(), 2)


class ReviewCard(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.target_date = datetime.date(1985, 5, 10)
        cls.days_from_memorization = 3
        cls.grade = 5
        cls.today = cls.target_date + timedelta(
            days=cls.days_from_memorization)

    def setUp(self):
        self.card = fake_data_objects.make_fake_card()
        self.user1, self.user2 = fake_data_objects.make_fake_users(2)

        with time_machine.travel(self.target_date):
            self.card_user_data = self.card.memorize(self.user1,
                                                     grade=self.grade)
            self.reference_card_user_data = CardUserData.objects.create(
                card=self.card,
                user=self.user2)

    def tearDown(self):
        self.card_user_data.delete()
        self.reference_card_user_data.delete()

    def test_deleting_review_data(self):
        """
        Card and user records shouldn't be affected by the deletion of
        a review data.
        """
        card_user_before_deleting = 2
        card_user_after_deleting = 1

        self.assertEqual(card_user_before_deleting,
                         CardUserData.objects.count())

        CardUserData.objects.get(card=self.card, user=self.user1).delete()

        self.assertEqual(card_user_after_deleting,
                         CardUserData.objects.count())
        self.assertTrue(all([self.user1.id, self.card.id]))

    def test_deleting_user(self):
        """
        Card should be left intact after deleting the user from a CardUserData
        instance object.
        """
        self.user1.delete()
        self.card.refresh_from_db()

        self.assertTrue(self.card.id)
        self.assertRaises(ObjectDoesNotExist,
                          self.card_user_data.refresh_from_db)

    def test_deleting_card(self):
        """
        A user instance should be left intact after deleting the card from
        a CardUserData instance object.
        """
        self.card.delete()
        self.user1.refresh_from_db()

        self.assertTrue(self.user1.id)
        self.assertRaises(ObjectDoesNotExist,
                          self.card_user_data.refresh_from_db)

    def test_introduced_on(self):
        self.assertIs(type(self.card_user_data.introduced_on),
                      datetime.datetime)
        self.assertEqual(self.card_user_data.introduced_on.date(),
                         self.target_date)

    def test_last_reviewed_default(self):
        """
        The field should be updated on a record creation and on each subsequent
        review.
        """
        self.assertEqual(self.card_user_data.last_reviewed, self.target_date)

    def test_computed_interval_default(self):
        expected_interval = 0
        self.assertEqual(self.reference_card_user_data.computed_interval,
                         expected_interval)

    def test_current_real_interval_default(self):
        with time_machine.travel(self.today):
            self.assertEqual(self.card_user_data.current_real_interval,
                             self.days_from_memorization)

    def test_review_date_default(self):
        self.assertEqual(self.reference_card_user_data.review_date,
                         self.target_date)

    def test_review_date_is_nullable(self):
        self.card_user_data.review_date = None
        self.assertRaises(IntegrityError,
                          lambda: raise_error(self.card_user_data.save))

    def test_default_lapses(self):
        """
        Default number of lapses in:
        * card memorized using the .memorize() method
        * CardUserData created manually
        """
        expected_lapses = 0
        self.assertEqual(self.card_user_data.lapses, expected_lapses)
        self.assertEqual(self.reference_card_user_data.lapses, expected_lapses)

    def test_lapses(self):
        """
        Failing a review should increase number of lapses by 1 (a failed review
        is the one with a grade < 3).
        """
        grade = 1
        expected_lapses = 1

        with time_machine.travel(self.card_user_data.review_date):
            review_data = self.card.review(self.user1, grade)

        self.assertEqual(review_data.lapses, expected_lapses)

    def test_reviewing_before_due_date(self):
        """
        Attempt to review a card before it's due date should raise an error.
        """
        target_date = self.card_user_data.review_date
        grade = 5

        with time_machine.travel(target_date):
            self.card_user_data.review(grade)

        def review_before_due():
            with time_machine.travel(target_date):
                self.card_user_data.review(grade)

        self.assertRaises(ReviewBeforeDue, review_before_due)


class ReviewsCounting(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.card = fake_data_objects.make_fake_card()
        cls.user = fake_data_objects.make_fake_user()

    def setUp(self):
        self.card_user_data = self.card.memorize(self.user)

    def tearDown(self):
        self.card_user_data.delete()

    def test_initial_total_reviews(self):
        """
        Total number of reviews after memorizing a card.
        """
        expected_number_of_reviews = 1
        self.assertEqual(self.card_user_data.total_reviews,
                         expected_number_of_reviews)

    def test_review_success_total_number(self):
        """
        Total number of reviews after a successful review.
        """
        expected_number_of_reviews = 2
        self._review_card(grade=3)
        self.assertEqual(self.card_user_data.total_reviews,
                         expected_number_of_reviews)

    def test_failed_review_total_number(self):
        """
        Total number of reviews after a failed review.
        """
        expected_number_of_reviews = 2
        self._review_card(grade=1)
        self.assertEqual(self.card_user_data.total_reviews,
                         expected_number_of_reviews)

    def _review_card(self, grade):
        with time_machine.travel(self.card_user_data.review_date):
            self.card_user_data.review(grade)


class CardsRedistributionMemorization(TestCase):
    """
    Selecting optimal date for reviewing newly memorized cards.
    Default review distribution range is 3 days.
    """

    @classmethod
    def setUpTestData(cls):
        cards_number = 7
        user = fake_data_objects.make_fake_user()
        cards = fake_data_objects.make_fake_cards(cards_number)
        for card in cards:
            card.memorize(user)

    def test_first_day(self):
        self._assert_reviews(days_delta=1, expected_cards_number=3)

    def test_second_day(self):
        self._assert_reviews(days_delta=2, expected_cards_number=2)

    def test_third_day(self):
        self._assert_reviews(days_delta=3, expected_cards_number=2)

    def test_fourth_day(self):
        self._assert_reviews(days_delta=4, expected_cards_number=0)

    def _assert_reviews(self, days_delta, expected_cards_number):
        review_date = date.today() + timedelta(days_delta)
        received_cards_number = CardUserData.objects.filter(
            review_date=review_date).count()
        self.assertEqual(received_cards_number, expected_cards_number)


class ReviewsRedistribution(TestCase):
    """
    Selecting an optimal review date for already memorized cards.
    """

    @classmethod
    def setUpTestData(cls):
        cls.cards = fake_data_objects.make_fake_cards(3)
        cls.user = fake_data_objects.make_fake_user()
        cls.memorized_date = datetime.date(1985, 3, 3)
        cls._memorize_cards()
        cls._review_cards()

    @classmethod
    def _memorize_cards(cls):
        review_date = cls.memorized_date + timedelta(1)

        with time_machine.travel(cls.memorized_date):
            for card in cls.cards:
                review = card.memorize(cls.user)
                review.review_date = review_date
                review.save()

    @classmethod
    def _review_cards(cls):
        grade = 4
        for card in cls.cards:
            review_data = CardUserData.objects.get(card=card, user=cls.user)
            with time_machine.travel(review_data.review_date):
                review_data.review(grade)

    def test_redistribution(self):
        # 1 day after memorization; 6 days - 1st (actual) review
        initial_review_date = self.memorized_date + timedelta(7)

        # after that, each card review date should be assigned one day
        # after the previous one (into the first free day):
        second_review_date = initial_review_date + timedelta(1)
        third_review_date = second_review_date + timedelta(1)
        reviews = self._get_sorted_reviews()

        self.assertEqual(reviews[0].review_date, initial_review_date)
        self.assertEqual(reviews[1].review_date, second_review_date)
        self.assertEqual(reviews[2].review_date, third_review_date)

    def _get_sorted_reviews(self):
        return sorted([CardUserData.objects.get(card=card, user=self.user)
                       for card in self.cards], key=lambda c: c.review_date)


class InvalidMemorizeReview(ABC, TestCase):
    """
    Top-level class for testing a card memorization and reviews.
    """

    @classmethod
    def setUpTestData(cls):
        cls.invalid_grade_message = "Grade should be a 0-5 integer."

    def setUp(self):
        self.user = fake_data_objects.make_fake_user()
        self.card = fake_data_objects.make_fake_card()

    def tearDown(self):
        self.user.delete()
        self.card.delete()

    def _test_grade_type_error(self, invalid_grade):
        self._assert_error(TypeError, invalid_grade)

    def _test_grade_value_error(self, invalid_grade):
        self._assert_error(ValueError, invalid_grade)

    def _assert_error(self, expected_exception, invalid_grade):
        with self.assertRaises(expected_exception) as e:
            self._raise_error(invalid_grade)
        self.assertEqual(str(e.exception), self.invalid_grade_message)

    def _raise_error(self, invalid_grade):
        pass


class InvalidMemorizeGrade(InvalidMemorizeReview):
    def test_grade_too_high(self):
        invalid_grade = 6
        self._test_grade_value_error(invalid_grade)

    def test_grade_too_low(self):
        invalid_grade = -1
        self._test_grade_value_error(invalid_grade)

    def test_float_grade(self):
        invalid_grade = 3.5
        self._test_grade_type_error(invalid_grade)

    def test_invalid_grade_type(self):
        invalid_grade = "4"
        self._test_grade_type_error(invalid_grade)

    def _raise_error(self, invalid_grade):
        self.card.memorize(self.user, grade=invalid_grade)


class InvalidReviewGrade(InvalidMemorizeReview):
    def setUp(self):
        super(InvalidReviewGrade, self).setUp()
        self.card.memorize(self.user)

    def test_grade_too_high(self):
        invalid_grade = 6
        self._test_grade_value_error(invalid_grade)

    def test_grade_too_low(self):
        invalid_grade = -1
        self._test_grade_value_error(invalid_grade)

    def test_float_grade(self):
        invalid_grade = 3.5
        self._test_grade_type_error(invalid_grade)

    def test_invalid_grade_type(self):
        invalid_grade = "4"
        self._test_grade_type_error(invalid_grade)

    def _raise_error(self, invalid_grade):
        self.card.review(self.user, grade=invalid_grade)


def raise_error(failing_transaction: Callable):
    """
    The reason for adding this function is explained here:
    TransactionManagementError "You can't execute queries until
    the end of the 'atomic' block" while using signals, but only during
    Unit Testing
    https://stackoverflow.com/questions/21458387/ ...
    """
    with transaction.atomic():
        failing_transaction()
