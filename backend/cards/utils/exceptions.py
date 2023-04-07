from django.db.utils import IntegrityError


class CardReviewDataExists(IntegrityError):
    """Exception for subsequent attempt to memorize card.
    """

    def __init__(self):
        self.message = ("Review data for a given user/data pair "
                        + "already exists.")
        super().__init__(self.message)


class ReviewBeforeDue(Exception):
    def __init__(self):
        self.message = "Reviewing before card's due review date is forbidden."
        super().__init__(self.message)
