from enum import Enum
from pyhocon import ConfigTree


class Lang(Enum):
    # Functions to mix in to to concrete language enum
    @classmethod
    def from_string(cls, string: str):
        for member in cls:
            if member.value == string.lower():
                return member
        return cls("unk")

    def __eq__(self, other):
        return (self.__class__.__name__ == other.__class__.__name__
                and self._name_ == other._name_
                and self._value_ == other._value_)


def from_config(language_config: ConfigTree) -> Enum:
    return Enum("Language", [lang for lang in language_config.items()] + [("Unknown", "unk")], type=Lang)
