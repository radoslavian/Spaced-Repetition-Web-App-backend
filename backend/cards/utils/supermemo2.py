"""
Adapted from SuperMemo 2 algorithm implementation.
Original project name: SuperMemo2
Original project copyright: 2020 Alan Kan
Original homepage: https://github.com/alankan886/SuperMemo2
"""


from math import ceil
from datetime import date, datetime, timedelta
from typing import Optional, Union

import attr


year_mon_day = "%Y-%m-%d"
mon_day_year = "%m-%d-%Y"
day_mon_year = "%d-%m-%Y"


@attr.s
class SM2:
    easiness = attr.ib(validator=attr.validators.instance_of(float))
    interval = attr.ib(validator=attr.validators.instance_of(int))
    repetitions = attr.ib(validator=attr.validators.instance_of(int))
    review_date = attr.ib(init=False)

    @staticmethod
    def first_review(
        quality: int,
        review_date: Optional[Union[date, str]] = None,
        date_fmt: Optional[str] = None,
    ) -> "SM2":
        if not review_date:
            review_date = date.today()

        if not date_fmt:
            date_fmt = year_mon_day

        return SM2(2.5, 0, 0).review(quality, review_date, date_fmt)

    def review(
        self,
        quality: int,
        review_date: Optional[Union[date, str]] = None,
        date_fmt: Optional[str] = None,
    ) -> "SM2":
        # TODO: shall assert/raise exception if "quality" (grade)
        # TODO: is out of 0-5 range (test 1st, then code)

        if not review_date:
            review_date = date.today()

        if not date_fmt:
            date_fmt = year_mon_day

        self.easiness += 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        if self.easiness < 1.3:
            self.easiness = 1.3

        if isinstance(review_date, str):
            review_date = datetime.strptime(review_date, date_fmt).date()

        if quality < 3:
            self.interval = 1
            self.repetitions = 0
        else:
            if self.repetitions == 0:
                self.interval = 1
            elif self.repetitions == 1:
                self.interval = 6
            else:
                self.interval = ceil(self.interval * self.easiness)

            self.repetitions = self.repetitions + 1

        review_date += timedelta(days=self.interval)
        self.review_date = review_date

        return self
