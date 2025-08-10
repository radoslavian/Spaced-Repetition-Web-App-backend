import hashlib
from datetime import datetime
from functools import reduce

from django.core.files import File

from ..apps import CardsConfig


encoding = CardsConfig.default_encoding


def hash_sha256(string_for_hashing):
    return hashlib.sha256(bytes(string_for_hashing, encoding)).hexdigest()


def today():
    return datetime.now().date()


def validate_grade(grade):
    message = "Grade should be a 0-5 integer."

    if type(grade) is not int:
        raise TypeError(message)
    if 0 > grade or grade > 5:
        raise ValueError(message)


def compose(*functions):
    """
    Multiple function composition.
    From https://mathieularose.com/function-composition-in-python
    Original author: Mathieu Larose
    """
    def compose2(f, g):
        return lambda x: f(g(x))

    return reduce(compose2, functions, lambda x: x)


def get_file_hash(file: File) -> str:
    get_hash = hashlib.sha1()
    if file.multiple_chunks():
        for chunk in file.chunks():
            get_hash.update(chunk)
    else:
        get_hash.update(file.read())
    return get_hash.hexdigest()


def make_saver(superclass, db_file_field: str,
               db_digest_field: str):
    """
    Returns method for getting sha1 file digest for
    Sound or Image instances.
    """
    def save(self, *args, **kwargs):
        file_field = getattr(self, db_file_field)
        # in order for this to work, a file_field has to be non-nullable!
        if file_field:
            with file_field.open('rb') as f:
                file_hash = get_file_hash(f)
                setattr(self, db_digest_field, file_hash)
                super(superclass, self).save(*args, **kwargs)
    return save