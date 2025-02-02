import hashlib
from datetime import datetime
from functools import reduce

from ..apps import CardsConfig

encoding = CardsConfig.default_encoding


def hash_sha256(string_for_hashing):
    return hashlib.sha256(bytes(string_for_hashing, encoding)).hexdigest()


def today():
    return datetime.now().date()


def validate_grade(grade):
    if 0 > grade or grade > 5 or type(grade) is not int:
        raise ValueError("Grade should be 0-5 integer.")


def compose(*functions):
    """
    Multiple function composition.
    From https://mathieularose.com/function-composition-in-python
    Original author: Mathieu Larose
    """
    def compose2(f, g):
        return lambda x: f(g(x))

    return reduce(compose2, functions, lambda x: x)
