from cards.management.fr_importer.items_importer.modules.imported_card import \
    ImportedCard
from cards.management.fr_importer.items_parser.modules.html_memorized_card import \
    HtmlFormattedMemorizedCard
from cards.models import CardUserData
from users.models import User


class ImportedMemorizedCard(ImportedCard):
    def __init__(self, card_object: HtmlFormattedMemorizedCard, user: User):
        super().__init__(card_object)
        super().save()
        self._review_details = self.set_review_details(
            card_object["review_details"], user)

    def set_review_details(self, review_details, user):
        user_review = CardUserData(card=self._card,
                                   user=user,
                                   **review_details)
        user_review.save()

        # overwriting auto_now_add, won't work otherwise
        CardUserData.objects.filter(
            user=user,
            card=self._card
        ).update(introduced_on=review_details["introduced_on"])
        return user_review
