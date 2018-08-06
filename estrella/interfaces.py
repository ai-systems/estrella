import logging
from abc import ABCMeta, abstractmethod
from enum import Enum
from operator import attrgetter
from typing import Collection, Dict, Type, Union, Callable, List


class Loggable:
    def __init__(self):
        self.logger = logging.getLogger(".".join((self.__module__, self.__class__.__name__)))


class Representable:
    """
    Representable mix-in. Classes inheriting from this mix-in will be represented based on the configuration.

    Classes providing a 'to_represent' collection attribute will be represented based on this collection.
    defaults to the whole dict.

    Classes providing a 'to_exclude' collection attribute will be presented based on the 'to_repesent' attributes
    absent in 'to_exclude' collection. Defaults to all attributes starting with "_".
    """

    def __repr__(self):
        to_represent: Collection = getattr(self, "to_represent", self.__dict__.keys())
        to_exclude = {"to_represent, to_exclude"}
        to_exclude.update(getattr(self, "to_exclude", [k for k in self.__dict__.keys() if k.startswith("_")]))
        return "{}({})".format(self.__class__.__name__,
                               ", ".join(
                                   "{}='{}'".format(k, self.__dict__[k]) for k in to_represent if k not in to_exclude)
                               )


class Readable(metaclass=ABCMeta):
    """
    Printable Interface. Classes implementing this interface must provide a pprint() function (short for pretty-print)
    which outputs the representation of the class in a nice, fancy and human-readable way.
    """

    @abstractmethod
    def pprint(self, **kwargs) -> str:
        pass


class Viewable(metaclass=ABCMeta):
    """
    Viewable interface. For now not used too much.
    """

    @classmethod
    def allowed_attributes(cls) -> Collection[str]:
        """
        Not used yet.
        :return:
        """
        # will be used for multiple views, safe(r) for predicates, etc
        pass

    @classmethod
    def allowed_links(cls) -> Collection[str]:
        """
        Not used yet.
        :return:
        """
        # will be used for multiple views, safe(r) hops, etc
        pass

    @classmethod
    @abstractmethod
    def creatable_from(cls) -> Dict[Type, Union[str, Callable]]:
        """
        Mapping from an object's type to either a string defining the attribute name of the object or a
        function defining how to create the view from the object otherwise.
        """
        pass

    @classmethod
    def get_factory_method(cls, view_type: Type) -> Callable:
        """
        Creates a factory method for a Viewable given a Type from which the view is to be created.
        Utilizes `creatable_from`.

        :param view_type: Type from which the view is going to be created.
        :return: Factory method to create the view.
        """
        v = cls.creatable_from().get(type(view_type), None)
        if isinstance(v, str):
            return attrgetter(v)
        elif isinstance(v, Callable):
            return v
        else:
            return None


class Labeled(Enum):
    """
    Abstract class describing an enumerable finite label to describe an object.

    Provides some convenience methods such as parsing from string, and embedding lookups (which are not yet used).
    """

    # metaclass

    # def __init__(self):
    #     super().__init__()
    #     self.embedding: Embedding = None
    #     self._collection = None

    def get_label(self):
        return self.value

    def get_top(self, k) -> List:
        pass

    def get_distribution(self) -> Dict:
        pass

    def get_weighted_embedding(self, top_k=None):
        pass

    @classmethod
    def from_string(cls, string: str):
        try:
            return cls(string)
        except:
            try:
                cls(string.lower())
            except:
                raise ValueError("Unknown label for class {}: {}".format(str(cls.__name__), string))
