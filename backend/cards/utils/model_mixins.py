import datetime
from django.db import models
from django.dispatch import receiver

from .helpers import hash_sha256
from ..apps import CardsConfig

encoding = CardsConfig.default_encoding


class TriggeredUpdatesMixin:
    """Database model mix-in for automatic updates of two fields:
    hash - of selected fields from the model
    last_modified - updated on each save.

    Both fields are expected on the model with following parameters:
    hash = models.CharField(max_length=64)
    last_modified = models.DateTimeField(auto_now=True)

    Fields for hashing should be enumerated as text strings in
    __hashed_fields__ model attribute.
    """
    def _get_string_for_hashing(self):
        hash_string = ""
        for field in self.__hashed_fields__:
            hash_string += str(getattr(self, field))
        return hash_string

    def _create_fields_hash(self):
        hashed_string = self._get_string_for_hashing()
        return hash_sha256(hashed_string)

    def _update_last_modified(self):
        """Updates last_modified field.

        Helper to abstract method .pre_save, shouldn't be called
        anywhere else.
        """
        self.last_modified = datetime.datetime.now()

    def _update_hash(self):
        """Updates sha256 hash of selected fields from the model."""
        self.hash = self._create_fields_hash()

    @staticmethod
    @receiver(models.signals.pre_save)
    def pre_save(sender, instance, **kwargs):
        """Updates selected fields in objects instantiated from classes inheriting
        from TriggeredUpdatesMixin on session commit (triggered by the 'save'
        method).
        """
        # TODO: check if doesn't affect performance (when number of
        # TODO: transactions increases)
        if isinstance(instance, TriggeredUpdatesMixin):
            instance._update_hash()
            instance._update_last_modified()


