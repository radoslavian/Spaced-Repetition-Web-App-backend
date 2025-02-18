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
    def current_computed_interval(self) -> int:
        return self._fr_review["ivl"]

    @property
    def last_real_interval(self) -> int:
        return self._fr_review["rllivl"]

    @property
    def easiness_factor(self) -> float:
        decimal_places = 2
        e_factor =  round(
            self.current_computed_interval / self.last_real_interval,
            decimal_places)
        return self._normalize_e_factor(e_factor)

    @staticmethod
    def _normalize_e_factor(e_factor) -> float:
        ef_max = 4.0
        ef_min = 1.4
        if e_factor > ef_max:
            return ef_max
        elif e_factor < ef_min:
            return ef_min
        return e_factor

    @property
    def crammed(self) -> bool:
        return self.grade < self.max_for_cram

    @staticmethod
    def keys() -> list[str]:
        return ['computed_interval', 'lapses', 'reviews', 'total_reviews',
                'last_reviewed', 'introduced_on', 'review_date', 'grade',
                'easiness_factor', 'crammed', 'comment']

    @property
    def values(self) -> list[Any]:
        return [
            self.current_computed_interval,
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
