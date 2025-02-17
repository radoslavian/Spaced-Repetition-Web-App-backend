import datetime
from datetime import datetime as dt, timedelta
from typing import Any


class UserReview:
    """
    Translates the fr user review fields (from the elements.xml file) for use
    in a local database.
    """
    def __init__(self, fr_review: dict, time_of_start: int):
        self._fr_review = fr_review
        self._epoch_time_of_start = time_of_start
        self.max_for_cram = 3

    @property
    def lapses(self) -> int:
        # FullRecall doesn't count lapses (failed repetitions)
        return 0

    @property
    def reviews(self) -> int:
        return self._fr_review["rp"]

    @property
    def total_reviews(self) -> int:
        return self.reviews

    @property
    def grade(self) -> int:
        return self._fr_review["gr"]

    @property
    def review_date(self) -> datetime.datetime:
        return self.time_of_start + timedelta(
            days=self._fr_review["stmtrpt"])

    @property
    def introduced_on(self) -> datetime.datetime:
        return dt.fromtimestamp(self._fr_review["id"])

    @property
    def last_reviewed(self) -> datetime.datetime:
        return self.review_date - timedelta(days=self._fr_review["ivl"])

    @property
    def time_of_start(self) -> datetime.datetime:
        return dt.fromtimestamp(self._epoch_time_of_start)

    @property
    def computed_interval(self) -> int:
        return self._fr_review["ivl"]

    @property
    def easiness_factor(self) -> float:
        computed_interval = self.computed_interval
        min_ef = 1.8
        average_ef = 2.0
        medium_ef = 2.5
        max_ef = 3.0

        invalid_interval = computed_interval < 1
        low_interval = 0 < computed_interval < 300
        average_interval = 300 <= computed_interval < 600
        medium_interval = 600 <= computed_interval < 1000

        if low_interval:
            return min_ef
        elif average_interval:
            return average_ef
        elif medium_interval:
            return medium_ef
        elif invalid_interval:
            raise ValueError(
                "The computed interval for the card {card} is {interval},"
                " which is invalid!".format(card=self._fr_review["id"],
                                            interval=self.computed_interval))
        return max_ef

    @property
    def crammed(self):
        if self.grade < self.max_for_cram:
            return True
        return False

    @staticmethod
    def keys() -> list[str]:
        return ['computed_interval', 'lapses', 'reviews', 'total_reviews',
                'last_reviewed', 'introduced_on', 'review_date', 'grade',
                'easiness_factor', 'crammed', 'comment']

    @property
    def values(self) -> list[Any]:
        return [
            self.computed_interval,
            self.lapses,
            self.reviews,
            self.total_reviews,
            self.last_reviewed,
            self.introduced_on,
            self.review_date,
            self.grade,
            self.easiness_factor,
            self.crammed,
            None  # comment
        ]

    def __getitem__(self, key: str) -> dict:
        return dict(zip(self.keys(), self.values))[key]
