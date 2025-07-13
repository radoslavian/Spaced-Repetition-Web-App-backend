from django.test import TestCase
from cards.models import CardUserData
from cards.tests.fake_data import make_fake_cards, make_fake_users


class CramQueue(TestCase):
    def setUp(self):
        self.card_1, self.card_2, self.card_3 = make_fake_cards(3)

    def test_cram(self):
        user = make_fake_users(1)[0]
        # TODO: split into several tests
        # TODO: following should go into setUp
        # memorizing adds cards to cram
        for card in self.card_1, self.card_2, self.card_3:
            card.memorize(user, 3)

        self.assertEqual(len(user.crammed_cards), 3)

        # removing from cram - status change
        card_review_data = CardUserData.objects.get(user=user,
                                                    card=self.card_1)
        self.assertTrue(card_review_data.crammed)
        status = card_review_data.remove_from_cram()
        self.assertFalse(status)
        self.assertEqual(len(user.crammed_cards), 2)
        self.assertFalse(card_review_data.crammed)

        # removing from cram - no status change
        status = card_review_data.remove_from_cram()
        self.assertFalse(status)  # card wasn't crammed

        # manually adding to cram
        status = card_review_data.add_to_cram()
        self.assertTrue(status)
        self.assertTrue(card_review_data.crammed)
