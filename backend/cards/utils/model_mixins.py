import datetime
import hashlib
from django.db import models
from django.dispatch import receiver
from ..apps import CardsConfig

encoding = CardsConfig.default_encoding


class TriggeredUpdatesMixin:
    def _get_string_for_hashing(self):
        hash_string = ""
        for field in self.__hashed_fields__:
            hash_string += str(getattr(self, field))
        return hash_string

    def _create_fields_hash(self):
        hashed_string = self._get_string_for_hashing()
        return hashlib.sha256(bytes(hashed_string, encoding)).hexdigest()

    def _update_hash(self):
        """Updates sha256 hash of selected fields from the model.

        Abstract helper to the .pre_save method, shouldn't be called
        anywhere else.
        """
        pass

    def _update_last_modified(self):
        """Updates last_modified field.

        Helper to abstract method .pre_save, shouldn't be called
        anywhere else.
        """
        self.last_modified = datetime.datetime.now()

    def _update_hash(self):
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
