import hashlib
from datetime import datetime

from ..apps import CardsConfig

encoding = CardsConfig.default_encoding


def hash_sha256(string_for_hashing):
    return hashlib.sha256(bytes(string_for_hashing, encoding)).hexdigest()


def today():
    return datetime.now().date()
