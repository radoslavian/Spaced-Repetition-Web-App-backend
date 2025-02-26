from cards.management.fr_importer.items_importer.modules.imported_card import \
    ImportedCard
from cards.management.fr_importer.items_parser.modules.html_memorized_card import \
    HtmlFormattedMemorizedCard
from cards.management.fr_importer.items_parser.modules.user_review import \
    UserReview
from cards.models import CardUserData
from users.models import User


class ImportedMemorizedCard(ImportedCard):
    def __init__(self, card_object: HtmlFormattedMemorizedCard, user: User):
        super().__init__(card_object)
        super().save()
        review_details = self.get_review_details(card_object["review_details"])
        self._review_details = self.set_review_details(review_details, user)

    def set_review_details(self, review_details, user):
        user_review = CardUserData(card=self._card,
                                   user=user,
                                   **review_details)
        user_review.save()

        # overwriting auto_now_add
        CardUserData.objects.filter(
            user=user,
            card=self._card
        ).update(introduced_on=review_details["introduced_on"])
        return user_review

    @staticmethod
    def get_review_details(user_review: UserReview) -> dict:
        """
        computed_interval in days has to be fixed into Integer as long as
        CardUserData.computed_interval field doesn't store timedelta data.
        """
        # CardUserData.computed_interval type has to be changed
        # into DurationField.
        computed_interval_days = int(user_review["computed_interval"].days)
        review_details = {**user_review,
                          "computed_interval": computed_interval_days}
        return review_details
