from abc import ABCMeta, abstractmethod
from typing import List

import estrella.interfaces
from estrella import util
from estrella.input.normalizers import Normalizer
from estrella.model.basic import Document


class FormatReader(estrella.interfaces.Loggable, metaclass=ABCMeta):
    def __init__(self, normalizer):
        """
        Reads and parses Words, Sentences and Documents from a raw text input (i.e. a string).

        :param normalizer: Config or actual instance of a normalizer.
        """
        super().__init__()
        if not isinstance(normalizer, Normalizer):
            self.normalizer: Normalizer = util.construct_from_config(normalizer, restrict_to=Normalizer,
                                                                     relative_import="estrella.input.normalizers")
        else:
            self.normalizer = normalizer

    @abstractmethod
    def create_doc(self, loaded_resource) -> Document:
        pass

    def read_resource(self, loaded_resource) -> List[Document]:
        return [self.create_doc(resource) for resource in loaded_resource]
