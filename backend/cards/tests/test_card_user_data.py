from django.test import TestCase
from cards.tests.fake_data import make_fake_cards, make_fake_users


class CramQueue(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.low_grade, cls.high_grade = 2, 5
        cls.card_1, cls.card_2, cls.card_3 = make_fake_cards(3)
        [cls.user] = make_fake_users(1)

    def setUp(self):
        self.crammed_card = self.card_1.memorize(self.user, self.low_grade)
        self.not_crammed_card = self.card_2.memorize(self.user,
                                                     self.high_grade)
        self.reference_card = self.card_3.memorize(self.user, self.low_grade)

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