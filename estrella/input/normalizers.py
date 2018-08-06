import logging
from abc import ABCMeta, abstractmethod
from unidecode import unidecode

import estrella.interfaces
from estrella import util
from estrella.model.basic import Document


class Normalizer(estrella.interfaces.Loggable, metaclass=ABCMeta):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def normalize(self, text):
        pass

    @abstractmethod
    def normalize_word(self, word):
        pass

    @abstractmethod
    def revert(self, document: Document) -> str:
        pass


class DefaultNormalizer(Normalizer):
    def revert(self, document: Document) -> str:
        return " ".join(w.text for w in document.words)

    def normalize(self, text):
        return " ".join(unidecode(text).split(" "))

    def normalize_word(self, word: str):
        return word.lower().strip()


class SlightlyBetterNormalizer(Normalizer):
    """
    Should normalize with respect to punctuation etc.
    """

    def normalize_word(self, word):
        pass

    def revert(self, document: Document) -> str:
        pass

    def normalize(self, text):
        pass
