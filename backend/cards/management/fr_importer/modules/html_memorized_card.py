from cards.management.fr_importer.modules.html_formatted_card import \
    HtmlFormattedCard
from cards.management.fr_importer.modules.user_review import UserReview


class HtmlFormattedMemorizedCard(HtmlFormattedCard):
    def __init__(self, card, time_of_start):
        card_copy = {**card}
        review_details = card_copy.pop("review_details")
        super().__init__(card_copy)
        self._review_details = UserReview(review_details, time_of_start)

    @staticmethod
    def keys():
        keys = HtmlFormattedCard.keys()
        return [*keys, "review_details"]

    def values(self):
        values = super().values()
        return [*values, dict(self._review_details)]


