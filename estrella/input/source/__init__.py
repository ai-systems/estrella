from abc import ABCMeta, abstractmethod
import logging
from typing import List

import estrella.interfaces
from estrella import util


class SourceReader(estrella.interfaces.Loggable, metaclass=ABCMeta):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def load(self, location) -> List:
        """
        Returns an iterable (even if only 1 file was loaded) loaded resource (such as contents of a file).
        :return:
        """
        pass
