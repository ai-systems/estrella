import logging
from abc import ABCMeta, abstractmethod
from typing import List

import estrella.interfaces
from estrella import util
from estrella.model.basic import Document


class Enricher(estrella.interfaces.Loggable, metaclass=ABCMeta):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def enrich(self, document: Document):
        pass
