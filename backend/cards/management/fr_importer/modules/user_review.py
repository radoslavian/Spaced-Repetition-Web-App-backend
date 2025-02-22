import datetime
from datetime import datetime as dt, timedelta
from typing import Any


class UserReview:
    """
    Translates the fr user review fields (from the elements.xml file) for use
    in a local database.
    """
    def __init__(self, fr_review: dict, time_of_start: int|str):
        self._fr_review = self.convert_values_into_integers(fr_review)
        self._epoch_time_of_start = int(time_of_start)
        self.max_for_cram = 3

    @staticmethod
    def convert_values_into_integers(fr_review):
        return {key: int(value) for key, value in fr_review.items()}

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
        return self.time_of_start + self.time_to_repeat

    @property
    def time_to_repeat(self) -> datetime.timedelta:
        return datetime.timedelta(days=self._fr_review["stmtrpt"])

    @property
    def introduced_on(self) -> datetime.datetime:
        return dt.fromtimestamp(self._fr_review["id"])

    @property
    def last_reviewed(self) -> datetime.datetime:
        return self.review_date - self.computed_interval

    @property
    def time_of_start(self) -> datetime.datetime:
        return dt.fromtimestamp(self._epoch_time_of_start)

    @property
    def computed_interval(self) -> datetime.timedelta:
        return datetime.timedelta(days=self._fr_review["ivl"])

    @property
    def last_real_interval(self) -> datetime.timedelta:
        return datetime.timedelta(days=self._fr_review["rllivl"])

    @property
    def easiness_factor(self) -> float:
        decimal_places = 2
        e_factor =  round(
            self.computed_interval / self.last_real_interval,
            decimal_places)
        return self._normalize_e_factor(e_factor)

    def _normalize_e_factor(self, new_e_factor) -> float:
        ef_max = 4.0
        ef_min = 1.4
        ef_for_special_case = 2.0

        if self._ef_special_case():
            return ef_for_special_case
        elif new_e_factor > ef_max:
            return ef_max
        elif new_e_factor < ef_min:
            return ef_min
        return new_e_factor

    def _ef_special_case(self) -> bool:
        """
        Special case ef - see the test: test_user_review.test_ef_special_case
        for details.
        """
        max_real_interval = timedelta(days=1000)
        min_computed_interval = timedelta(days=500)
        special_case = (
                max_real_interval < self.last_real_interval >
                self.computed_interval > min_computed_interval
                and self.grade > 3 and self.reviews > 3)
        return special_case

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

    def __str__(self):
        return "\n".join(f"{key}: {self[key]}" for key in self.keys())

    def __getitem__(self, key: str) -> dict:
        return dict(zip(self.keys(), self.values))[key]
