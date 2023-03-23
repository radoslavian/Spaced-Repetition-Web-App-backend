from datetime import timedelta, date, datetime
from random import randint
import django.db.utils
import time_machine
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from .models import (Card, Template, Category, CardComment, ReviewDataSM2,
                     Image, CardImage)
from faker import Faker
from django.core.files.uploadedfile import SimpleUploadedFile
from .utils.exceptions import CardReviewDataExists
from .utils.helpers import today
import datetime

fake = Faker()


# Create your tests here.

class ExceptionTests(TestCase):
    def test_CardReviewDataExists_message(self):
        expected_message = ("Review data for a given user/data pair "
                            + "already exists.")
        self.assertEqual(CardReviewDataExists().message, expected_message)


class TemplateModelTests(TestCase):
    def setUp(self):
        self.template_title = fake.text(60)
        self.description = fake.text(300)
        self.body = fake.text(300)

        self.template = Template.objects.create(
            title=self.template_title,
            description=self.description,
            body=self.body
        )

    def test_duplicate_template(self):
        def duplicate_template():
            template = Template.objects.create(
                title=self.template_title,
                description=self.description,
                body=self.body
            )
            template.save()

        self.assertRaises(django.db.utils.IntegrityError, duplicate_template)

    @staticmethod
    def test_uuids():
        """Check if constructor doesn't duplicate uuids, which could happen
        if function for creating uuid is passed wrong: ie
        value returned from the function is passed instead
        of a callable function object.
        """
        for i in range(3):
            Template.objects.create(
                title=fake.text(15),
                description=fake.text(20),
                body=fake.text(20)
            )

    def test_last_modified_update(self):
        """Test if last_modified attribute changes when modified.
        """
        prev_last_modified = self.template.last_modified
        self.template.front = "New test card's question."
        self.template.save()

        self.assertNotEqual(self.template.last_modified, prev_last_modified)

    def test_serialization(self):
        expected_serialization = f"<{self.template_title}>"
        actual_serialization = str(self.template)
        self.assertEqual(actual_serialization, expected_serialization)


class CardModelTests(TestCase):
    def setUp(self):
        self.front = "Test card's question."
        self.back = "Test card's answer."

        self.card = Card.objects.create(
            front=self.front,
            back=self.back
        )

    def test_duplicate_card(self):
        def duplicate_card():
            card = Card.objects.create(
                front=self.front,
                back=self.back
            )
            card.save()

        self.assertRaises(django.db.utils.IntegrityError, duplicate_card)

    @staticmethod
    def test_uuids():
        for i in range(3):
            Template.objects.create(
                title=fake.text(15),
                description=fake.text(20),
                body=fake.text(20)
            )

    def test_last_modified_update(self):
        """Test if last_modified attribute changes when modified.
        """
        prev_last_modified = self.card.last_modified
        self.card.front = "New test card's question."
        self.card.save()

        self.assertNotEqual(self.card.last_modified, prev_last_modified)

    def test_serialization(self):
        expected_serialization = "Card(Q: Test card's question.; " \
                                 "A: Test card's answer.)"
        actual_serialization = str(self.card)
        self.assertEqual(actual_serialization, expected_serialization)


class TemplateCardRelationshipTests(TemplateModelTests, CardModelTests):
    def setUp(self):
        TemplateModelTests.setUp(self)
        CardModelTests.setUp(self)
        card = Card.objects.first()
        card.template = Template.objects.first()
        card.save()

    def test_add_template_to_card(self):
        card, template = self._get_tested_objects()
        card.template = template
        card.save()

        self.assertTrue(card.template is template)
        self.assertTrue(card.template_id == template.id)

    def test_card_related_name(self):
        card, template = self._get_tested_objects()
        card_from_template = template.cards.first()

        self.assertEqual(card_from_template.front, card.front)

    @staticmethod
    def _get_tested_objects():
        card = Card.objects.first()
        template = Template.objects.first()

        return card, template

    def test_remove_template_from_card(self):
        card, template = self._get_tested_objects()
        card.template = None
        card.save()

        self.assertFalse(card.template is template)
        self.assertTrue(Template.objects.get(title=self.template_title))
        self.assertFalse(card.template)
        self.assertFalse(card.template_id == template.id)

    def test_removing_template(self):
        card, template = self._get_tested_objects()

        self.assertRaises(ProtectedError, template.delete)

        # remove reference to the template and delete it:
        card.template = None
        card.save()
        template.delete()

        self.assertRaises(
            ObjectDoesNotExist,
            lambda: Template.objects.get(title=self.template_title))


class CategoryTests(TestCase):
    def setUp(self):
        CATEGORY_NAME_LEN = 20
        self.first_category_name = fake.text(CATEGORY_NAME_LEN)
        self.second_category_name = fake.text(CATEGORY_NAME_LEN)
        self.third_category_name = fake.text(CATEGORY_NAME_LEN)

        first_category = Category.objects.create(
            name=self.first_category_name
        )
        Category.objects.create(
            name=self.second_category_name,
            parent=first_category
        )
        Category.objects.create(
            parent=first_category,
            name=self.third_category_name
        )

    @staticmethod
    def test_uuids():
        for i in range(3):
            Category.objects.create(name=fake.text(15))

    def test_serialization(self):
        category = Category.objects.first()
        expected_serialization = f"<{category.name}>"

        self.assertEqual(expected_serialization, str(category))

    def test_self_reference(self):
        NUMBER_OF_SUB_CATEGORIES = 2
        first_category = self.get_category(self.first_category_name)
        second_category = self.get_category(self.second_category_name)

        self.assertEqual(first_category.sub_categories.count(),
                         NUMBER_OF_SUB_CATEGORIES)
        self.assertEqual(second_category.parent.name,
                         self.first_category_name)

    def test_deleting_empty_subcategory(self):
        first_category = self.get_category(self.first_category_name)
        for sub_category in first_category.sub_categories.all():
            sub_category.delete()

        self.assertRaises(
            ObjectDoesNotExist,
            lambda: self.get_category(self.second_category_name))

        # as stated in the documentation, treebeard relies on raw
        # SQL expressions to manage model, so after applying changes model
        # requires re-fetch from the database in order to stay up-to-date
        self.assertTrue(self.get_category(self.first_category_name))

    def test_deleting_non_empty_top_category(self):
        first_category = self.get_category(self.first_category_name)

        self.assertRaises(ProtectedError, first_category.delete)

    def test_emptying_and_deleting(self):
        """Test deleting top category after clearing subcategories.
        """
        first_category = self.get_category(self.first_category_name)
        first_category.sub_categories.set([])
        first_category.save()

        self.assertTrue(first_category.delete())
        self.assertTrue(all([self.get_category(self.second_category_name),
                             self.get_category(self.third_category_name)]))

    def test_duplicate_category(self):
        """Attempt to add same-named sibling category.
        """
        parent_category = self.get_category(self.first_category_name)
        new_category = Category(name=self.second_category_name)
        new_category.save()

        def duplicate_category():
            parent_category.sub_categories.add(new_category)
            parent_category.save()

        self.assertRaises(django.db.utils.IntegrityError, duplicate_category)

    @staticmethod
    def get_category(name: str):
        return Category.objects.get(name=name)


class CategoryJoinsTests(TestCase):
    def test_skipped_categories(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(username=fake.text(6))
        parent_category = Category(name="Parent category")
        first_subcategory = Category(
            name="first subcategory",
            parent=parent_category
        )
        parent_category.save()
        first_subcategory.save()
        user.skipped_categories.add(first_subcategory)
        user.save()

        self.assertEqual(first_subcategory.skipping_users.first().username,
                         user.username)
        self.assertEqual(user.skipped_categories.first().name,
                         first_subcategory.name)

    def test_ignored_cards(self):
        user_model = get_user_model()
        user = user_model(username=fake.text(6))
        user.save()
        card = Card(
            front=fake.text(100),
            back=fake.text(100)
        )
        card.save()
        user.ignored_cards.add(card)

        self.assertEqual(user.ignored_cards.first().front,
                         card.front)
        self.assertEqual(card.ignoring_users.first().username,
                         user.username)


class FakeUsersCards(TestCase):
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

    @staticmethod
    def get_users():
        """Returns two example users.
        """
        user_1 = CramQueueTests.user_model.objects.get(username="first_user")
        user_2 = CramQueueTests.user_model.objects.get(username="second_user")
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


class CramQueueTests(FakeUsersCards):
    def test_add_card_to_cram(self):
        user_1, user_2 = self.get_users()
        card_1, card_2, card_3 = self.get_cards()

        user_1.cram_queue.add(card_1, card_2)
        user_2.cram_queue.add(card_3, card_2)

        self.assertEqual(card_1.cramming_users.count(), 1)
        self.assertEqual(card_2.cramming_users.count(), 2)

        # check users of the 2nd card:
        card_2_cramming_users = card_2.cramming_users.all()
        card_2_cramming_users_names = [user.username
                                       for user in card_2_cramming_users]
        self.assertTrue(user_1.username in card_2_cramming_users_names)
        self.assertTrue(user_2.username in card_2_cramming_users_names)

    def test_remove_card_from_cram(self):
        user_1, user_2 = self.get_users()
        card_1, card_2, card_3 = self.get_cards()

        user_1.cram_queue.add(card_1, card_2)
        user_2.cram_queue.add(card_3, card_2)

        # switch set([]) to clear()
        card_3.cramming_users.set([])
        card_3.save()

        self.assertEqual(user_2.cram_queue.count(), 1)
        self.assertEqual(user_2.cram_queue.first().front, card_2.front)


class CardCommentsTests(FakeUsersCards):
    def setUp(self):
        super().setUp()
        self.fake_comment_len = randint(10, 100)
        self.comment1_text = fake.text(self.fake_comment_len)
        self.comment2_text = fake.text(self.fake_comment_len)

    def test_add_comment(self):
        card, user_1, user_2 = self.get_card_users_with_comments()
        card_comment = CardComment.objects.get(card=card, user=user_2)

        self.assertEqual(card_comment.text, self.comment2_text)
        self.assertEqual(user_1.commented_cards.count(), 1)
        self.assertEqual(card.commenting_users.count(), 2)
        self.assertEqual(user_2.cardcomment_set.get(card=card).text,
                         self.comment2_text)

    def test_remove_comment(self):
        card, user_1, user_2 = self.get_card_users_with_comments()

        self.assertEqual(user_1.commented_cards.count(), 1)
        card.commenting_users.clear()
        self.assertEqual(user_1.commented_cards.count(), 0)
        self.assertTrue(all([card.id, user_1.id, user_2.id]))
        self.assertRaises(ObjectDoesNotExist,
                          lambda: CardComment.objects.get(
                              user=user_1, card=card))

    def test_uniqueness(self):
        """Test for uniqueness of user/card pair.
        """
        card, user_1, _ = self.get_card_users_with_comments()
        self.assertRaises(django.db.utils.IntegrityError,
                          CardComment(card=card, user=user_1).save)

    def test_update_comment(self):
        card, user_1, user_2 = self.get_card_users_with_comments()
        card_comment = CardComment.objects.get(user=user_1,
                                               card=card)
        card_comment.text = "new text"
        card_comment.save()

        self.assertEqual(user_1.cardcomment_set.get(card=card).text,
                         card_comment.text)
        self.assertNotEqual(user_2.cardcomment_set.get(card=card).text,
                            card_comment.text)

    def add_comments(self, card, user_1, user_2):
        CardComment(user=user_1,
                    text=self.comment1_text,
                    card=card).save()
        CardComment(user=user_2,
                    text=self.comment2_text,
                    card=card).save()

    def get_card_users_with_comments(self):
        user_1, user_2 = self.get_users()
        card = self.get_cards()[0]
        self.add_comments(card, user_1, user_2)
        return card, user_1, user_2


class CardReviewsTests(FakeUsersCards):
    def test_no_user_foreign_keys_in_join_table(self):
        card, *_ = self.get_cards()
        self.assertRaises(django.db.utils.IntegrityError,
                          lambda: self.raise_error(
                              ReviewDataSM2.objects.create(card=card).save))

    def test_no_card_foreign_key_in_join_table(self):
        user, _ = self.get_users()
        self.assertRaises(django.db.utils.IntegrityError,
                          lambda: self.raise_error(
                              ReviewDataSM2.objects.create(user=user).save))

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
        ReviewDataSM2(card=card, user=user).save()

        self.assertRaises(django.db.utils.IntegrityError,
                          ReviewDataSM2(card=card, user=user).save)

    def test_backrefs(self):
        card, *_ = self.get_cards()
        user1, user2 = self.get_users()
        ReviewDataSM2(card=card, user=user1).save()
        ReviewDataSM2(card=card, user=user2).save()

        self.assertEqual(card.reviewing_users.get(id=user1.id).username,
                         user1.username)
        self.assertEqual(user2.cards_review_data.get(id=card.id).front,
                         card.front)
        self.assertEqual(card.reviewing_users.count(), 2)
        self.assertEqual(user1.cards_review_data.count(), 1)
        self.assertEqual(user1.cards_review_data.first().front,
                         card.front)

    def test_deleting_reviews_data(self):
        card, *_ = self.get_cards()
        user1, user2 = self.get_users()
        ReviewDataSM2(card=card, user=user1).save()
        ReviewDataSM2.objects.get(card=card, user=user1).delete()

        self.assertTrue(all([user1.id, card.id]))
        self.assertEqual(ReviewDataSM2.objects.count(), 0)

    def test_deleting_users_cards(self):
        card, user = self.get_card_user()
        ReviewDataSM2(card=card, user=user).save()
        user.delete()

        self.assertFalse(ReviewDataSM2.objects.first())
        self.assertTrue(card.id)

    def test_introduced_on_field(self):
        review_data = self.get_review_data()
        review_data.save()

        self.assertEqual(review_data.introduced_on, today())

    def test_last_reviewed_default(self):
        card, user = self.get_card_user()
        ReviewDataSM2(card=card, user=user).save()

        # the field shall be updated on introduction and on each review
        self.assertEqual(ReviewDataSM2.objects.first().last_reviewed,
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
        self.assertEqual(review_data.repetitions, 1)

    def test_default_grade(self):
        review_data = self.get_review_data()
        default_grade = 4

        self.assertEqual(review_data.grade, default_grade)

    def get_review_data(self):
        card, user = self.get_card_user()
        review_data = ReviewDataSM2(card=card, user=user)
        return review_data

    def test_memorize_card(self):
        card, user = self.get_card_user()
        grade = 4
        easiness_factor = 2.5
        review_data_from_return = card.memorize(user, grade=grade)
        review_data = ReviewDataSM2.objects.get(card=card, user=user)

        self.assertEqual(review_data_from_return, review_data)
        self.assertEqual(review_data.repetitions, 1)
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
            "repetitions": first_review.repetitions,
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
        first_review = card.memorize(user, grade=4)

        with time_machine.travel(destination_date):
            self.assertEqual(first_review.current_real_interval,
                             days_delta)

            second_review = card.review(user=user, grade=3)
            second_review_obtained_data = {
                "introduced_on": second_review.introduced_on,
                "easiness": second_review.easiness_factor,
                "last_reviewed": second_review.last_reviewed,
                "grade": second_review.grade,
                "last_comp_interval": second_review.computed_interval,
                "repetitions": second_review.repetitions,
                "next_review": second_review.review_date
            }
            second_review_expected_data = {
                "introduced_on": today() - timedelta(days_delta),
                "easiness": 2.36,
                "last_reviewed": date.today(),
                "grade": 3,
                "last_comp_interval": 6,
                "repetitions": 2,
                "next_review": (today() + timedelta(6))
            }

        self.assertDictEqual(second_review_obtained_data,
                             second_review_expected_data)

    def test_subsequent_reviews(self):
        card, user = self.get_card_user()
        grades = (3, 4, 5, 3, 2, 4,)
        expected_comp_intervals = (6, 38, 114, 306, 1, 1,)

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
            lambda: ReviewDataSM2.objects.get(user=user, card=card))

    def test_forgetting_non_existent_relationship(self):
        """Attempt to forget (remove from the learning process)
        non-existent card/user combination.
        """
        user_1, user_2 = self.get_users()
        card, *_ = self.get_cards()
        card.memorize(user_1)

        self.assertRaises(ObjectDoesNotExist, lambda: card.forget(user_2))

    def test_ReviewDataSM2_serialization(self):
        card, user = self.get_card_user()
        card.memorize(user)
        review_data = ReviewDataSM2.objects.get(user=user, card=card)
        expected_rdsm2_serialization = \
            f"ReviewDataSM2(user='{str(user)}' card='{str(card)}')"

        self.assertEqual(expected_rdsm2_serialization,
                         str(review_data))

    def test_selecting_optimal_date_after_memorizing(self):
        cards_number = 7
        user, _ = self.get_users()
        cards = [Card(**self.fake_card_data()) for i in range(cards_number)]
        for card in cards:
            card.save()
            card.memorize(user)

        first_day = ReviewDataSM2.objects.filter(
            review_date=date.today() + timedelta(1)).count()
        second_day = ReviewDataSM2.objects.filter(
            review_date=date.today() + timedelta(2)).count()
        third_day = ReviewDataSM2.objects.filter(
            review_date=date.today() + timedelta(3)).count()
        fourth_day = ReviewDataSM2.objects.filter(
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

        reviews_last_day = ReviewDataSM2.objects.filter(
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

    def test_intervals_simulation_after_memorization(self):
        card, user = self.get_card_user()
        review_date = datetime.date.today() + datetime.timedelta(days=1)
        expected_output = {
            0: dict(
                easiness=1.7000000000000002, interval=1, repetitions=0,
                review_date=review_date
            ),
            1: dict(
                easiness=1.96, interval=1, repetitions=0,
                review_date=review_date
            ),
            2: dict(
                easiness=2.1799999999999997, interval=1, repetitions=0,
                review_date=review_date
            ),
            3: dict(
                easiness=2.36, interval=1, repetitions=1,
                review_date=review_date
            ),
            4: dict(
                easiness=2.5, interval=1, repetitions=1,
                review_date=review_date
            ),
            5: dict(
                easiness=2.6, interval=1, repetitions=1,
                review_date=review_date
            )
        }
        simulation = card.simulate_reviews(user)

        self.assertDictEqual(expected_output, simulation)

    def test_intervals_simulation_after_second_review(self):
        card, user = self.get_card_user()
        card.memorize(user, grade=4)
        next_review_failed = datetime.date.today() + timedelta(days=1)
        next_review_success = datetime.date.today() + timedelta(days=6)
        simulation = card.simulate_reviews(user)
        expected_output = {
            0: {'easiness': 1.7000000000000002, 'interval': 1,
                'repetitions': 0, 'review_date': next_review_failed},
            1: {'easiness': 1.96, 'interval': 1, 'repetitions': 0,
                'review_date': next_review_failed},
            2: {'easiness': 2.1799999999999997, 'interval': 1,
                'repetitions': 0, 'review_date': next_review_failed},
            3: {'easiness': 2.36, 'interval': 6, 'repetitions': 2,
                'review_date': next_review_success},
            4: {'easiness': 2.5, 'interval': 6, 'repetitions': 2,
                'review_date': next_review_success},
            5: {'easiness': 2.6, 'interval': 6, 'repetitions': 2,
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
        next_review_success = review_date + timedelta(days=138)
        expected_output = {
            0: {'easiness': 1.3,
                'interval': 1,
                'repetitions': 0,
                'review_date': next_review_failed},
            1: {'easiness': 1.3999999999999997,
                'interval': 1,
                'repetitions': 0,
                'review_date': next_review_failed},
            2: {'easiness': 1.6199999999999997,
                'interval': 1,
                'repetitions': 0,
                'review_date': next_review_failed},
            3: {'easiness': 1.7999999999999998,
                'interval': 138,
                'repetitions': 6,
                'review_date': next_review_success},
            4: {'easiness': 1.9399999999999997,
                'interval': 138,
                'repetitions': 6,
                'review_date': next_review_success},
            5: {'easiness': 2.0399999999999996,
                'interval': 138,
                'repetitions': 6,
                'review_date': next_review_success}}

        self.assertDictEqual(expected_output, simulation)


class CardsImagesTests(FakeUsersCards):
    def test_add_single_image_to_card(self):
        card, *_ = self.get_cards()
        image1_in_database = self.get_image_instance()
        image2_in_database = self.get_image_instance()
        card_front_image = CardImage(card=card,
                                     image=image1_in_database,
                                     side="front")
        card_front_image.save()
        self.assertEqual(card.images.count(), 1)
        self.assertEqual(image1_in_database.cards.count(), 1)

        card_back_image = CardImage(card=card,
                                    image=image2_in_database,
                                    side="back")
        card_back_image.save()
        self.assertEqual(card.images.count(), 2)

        # card.front_images, card.back_images - properties
        self.assertEqual(len(card.front_images), 1)
        self.assertEqual(len(card.back_images), 1)

    def test_remove_card_to_image(self):
        """Test deleting image from the card, should keep image file entry
         in the database.
        """
        card, *_ = self.get_cards()
        image_in_database = self.get_image_instance()
        card_image = CardImage(card=card,
                               image=image_in_database,
                               side="front")
        card_image.save()
        card_image.delete()

        self.assertTrue(card.id)

        card.delete()
        self.assertFalse(card_image.id)
        self.assertTrue(image_in_database.id)

    def test_uniqueness_card_image_side(self):
        card, *_ = self.get_cards()
        image_in_database = self.get_image_instance()

        def add_once(side):
            card_image = CardImage(card=card,
                                   image=image_in_database,
                                   side=side)
            card_image.save()

        add_once("front")
        self.assertRaises(django.db.utils.IntegrityError,
                          lambda: add_once("front"))

    def test_uniqueness_card_image(self):
        """As opposite to test_uniqueness_card_image_side,
        the test shouldn't raise exception after adding twice Card/Image
        relationship, but with different 'side' value.
        """
        card, *_ = self.get_cards()
        image_in_database = self.get_image_instance()

        CardImage(card=card,
                  image=image_in_database,
                  side="front").save()
        CardImage(card=card,
                  image=image_in_database,
                  side="back").save()

    def test_side_check_constraint(self):
        card, *_ = self.get_cards()
        image_in_database = self.get_image_instance()

        self.assertRaises(
            django.db.utils.IntegrityError,
            CardImage(card=card, image=image_in_database, side="fff").save)

    @staticmethod
    def get_image_instance():
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01'
            b'\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00'
            b'\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        image = SimpleUploadedFile(name=fake.file_name(extension="gif"),
                                   content=small_gif,
                                   content_type="image/gif")
        image_in_database = Image(image=image,
                                  description=fake.text(999))
        image_in_database.save()
        return image_in_database
