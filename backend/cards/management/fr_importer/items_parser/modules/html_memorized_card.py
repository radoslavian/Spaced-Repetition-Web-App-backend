from cards.management.fr_importer.items_parser.modules.html_formatted_card import \
    HtmlFormattedCard
from cards.management.fr_importer.items_parser.modules.item import Item
from cards.management.fr_importer.items_parser.modules.user_review import UserReview


class HtmlFormattedMemorizedCard(HtmlFormattedCard):
    def __init__(self, item: dict|Item, time_of_start: int):
        review_details = item["review_details"]
        super().__init__(item)
        self._review_details = UserReview(review_details, time_of_start)

    @staticmethod
    def keys() -> list[str]:
        keys = HtmlFormattedCard.keys()
        return [*keys, "review_details"]

    def values(self) -> list[dict]:
        values = super().values()
        return [*values, dict(self._review_details)]


