import hashlib
from datetime import datetime

from ..apps import CardsConfig

encoding = CardsConfig.default_encoding


def hash_sha256(hashed_string):
    return hashlib.sha256(bytes(hashed_string, encoding)).hexdigest()


def today():
    return datetime.now().date()
