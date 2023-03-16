from django.db.utils import IntegrityError


class CardReviewDataExists(IntegrityError):
    """Exception for subsequent attempt to memorize card.
    """
    def __init__(self):
        self.message = ("Review data for a given user/data pair "
                        + "already exists.")
        super().__init__(self.message)
