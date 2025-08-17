"""
The Card.simulation() method returns an approximate (calculated without
consideration for cards already assigned for given dates) review data
after evaluating a card repetition. The method doesn't mutate any data in a
database.
This data can in turn be used in the UI as a user feedback.
"""
import datetime
from abc import ABC, abstractmethod
from typing import Dict

import time_machine
from django.test import TestCase

from cards.tests.fake_data import fake_data_objects
from cards.utils.supermemo2 import SM2


class SMSimulation(ABC):
    simulation: Dict

    @classmethod
    def setup_initial_data(cls):
        cls.card = fake_data_objects.make_fake_card()
        cls.user = fake_data_objects.make_fake_user()
        cls.initial_grade = 4
        cls.memorization_date = datetime.date(2021, 5, 10)

    @abstractmethod
    def review_card(self, grade):
        pass

    def assert_grade(self, grade):
        expected_output = self.review_card(grade=grade)
        received_output = self.simulation[grade]
        self.assertDictEqual(expected_output, received_output)

    def assertDictEqual(self, *args, **kwargs):
        TestCase.assertDictEqual(self, *args, **kwargs)

    @staticmethod
    def repetition_to_dict(repetition):
        review = {
            'easiness': repetition.easiness,
            'interval': repetition.interval,
            'reviews': repetition.repetitions,
            'review_date': repetition.review_date
        }
        return review


class BeforeMemorizationSimulation(SMSimulation, TestCase):
    """
    Simulate review data for queued cards waiting for memorization.
    The output for a not-yet-memorized card should correspond with
    the SM2.first_review().
    """

    @classmethod
    def setUpTestData(cls):
        cls.setup_initial_data()

        with time_machine.travel(cls.memorization_date):
            cls.simulation = cls.card.simulate_reviews(cls.user)

    def test_null(self):
        null_grade = 0
        self.assert_grade(null_grade)

    def test_bad(self):
        bad_grade = 1
        self.assert_grade(bad_grade)

    def test_fail(self):
        fail_grade = 2
        self.assert_grade(fail_grade)

    def test_pass(self):
        pass_grade = 3
        self.assert_grade(pass_grade)

    def test_good(self):
        good_grade = 4
        self.assert_grade(good_grade)

    def test_ideal(self):
        ideal_grade = 5
        self.assert_grade(ideal_grade)

    def review_card(self, grade):
        repetition = SM2.first_review(quality=grade,
                                      review_date=self.memorization_date)
        review = self.repetition_to_dict(repetition)
        return review

    def assert_grade(self, grade):
        expected_output = self.review_card(grade=grade)
        received_output = self.simulation[grade]
        self.assertDictEqual(expected_output, received_output)


class ReviewSimulation(SMSimulation, TestCase):
    """
    Card.simulate_reviews() uses CardUserData instance attributes for
    calculating approximate next review.
    """
    @classmethod
    def setUpTestData(cls):
        cls.setup_initial_data()

        with time_machine.travel(cls.memorization_date):
            cls.review_data = cls.card.memorize(cls.user,
                                                grade=cls.initial_grade)

        with time_machine.travel(cls.review_data.review_date):
            cls.simulation = cls.card.simulate_reviews(cls.user)

    def test_null(self):
        null_grade = 0
        self.assert_grade(null_grade)

    def test_bad(self):
        bad_grade = 1
        self.assert_grade(bad_grade)

    def test_fail(self):
        fail_grade = 2
        self.assert_grade(fail_grade)

    def test_pass(self):
        pass_grade = 3
        self.assert_grade(pass_grade)

    def test_good(self):
        good_grade = 4
        self.assert_grade(good_grade)

    def test_ideal(self):
        ideal_grade = 5
        self.assert_grade(ideal_grade)

    def review_card(self, grade):
        repetition = SM2(self.review_data.easiness_factor,
                         self.review_data.current_real_interval,
                         self.review_data.reviews) \
            .first_review(quality=self.initial_grade,
                          review_date=self.memorization_date)

        review = repetition.review(grade, review_date=repetition.review_date)
        return self.repetition_to_dict(review)