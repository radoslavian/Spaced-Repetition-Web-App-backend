from abc import ABC, abstractmethod


class CardManager(ABC):
    @abstractmethod
    def save_cards(self):
        pass