import datetime
from django.db import models
from django.dispatch import receiver
from ..apps import CardsConfig

encoding = CardsConfig.default_encoding


class TriggeredLastModifiedUpdateMixin:
    """Database model mix-in for automatic updates the last_modified field,
    updated on each save.

    expects following field on the model:
    last_modified = models.DateTimeField(auto_now=True)
    """

    def _update_last_modified(self):
        """Updates last_modified field.

        Helper to abstract method .pre_save, shouldn't be called
        anywhere else.
        """
        self.last_modified = datetime.datetime.now()

    @staticmethod
    @receiver(models.signals.pre_save)
    def pre_save(sender, instance, **kwargs):
        """Updates selected fields in objects instantiated from classes
        inheriting from TriggeredLastModifiedUpdateMixin on session commit
        (triggered by the 'save' method).
        """
        # TODO: check if doesn't affect performance (when number of
        # TODO: transactions increases)
        if isinstance(instance, TriggeredLastModifiedUpdateMixin):
            instance._update_last_modified()
