from collections import Sequence
from typing import List, Collection, Dict, Type, Union, Callable
from uuid import uuid4

from estrella.interfaces import Representable, Readable, Viewable, Labeled, Numeric


class Document(Sequence, Representable, Readable, Viewable):

    @classmethod
    def allowed_attributes(cls) -> Collection[str]:
        pass

    @classmethod
    def allowed_links(cls) -> Collection[str]:
        pass

    @classmethod
    def creatable_from(cls) -> Dict[Type, Union[str, Callable]]:
        from estrella.main import Estrella
        return {
            Estrella: "_docs"
        }

    def pprint(self, **kwargs):
        return "\n".join(s.pprint(**kwargs) for s in self.sentences)

    def __getitem__(self, i: int):
        return self.sentences[i]

    def __len__(self) -> int:
        return len(self.sentences)

    def __init__(self, sentences):
        self.name: str = None
        self.id: uuid4 = None
        self.genre: Labeled = None  # will be enriched
        self.language = None  # will be enriched
        self.sentences: List[Sentence] = sentences
        self._text = None

    @property
    def words(self) -> list:
        return [word for sentence in self.sentences for word in sentence]

    def with_view(self, span_view: type, *args):
        # create a working copy of the containing spans to work on
        pass

    @property
    def plaintext(self) -> str:
        """
        Just return the plain text representation
        :return:
        """
        if not self._text:
            raise NotImplementedError()  # create self._text
        return self._text


class Sentence(Sequence, Representable, Readable):
    def pprint(self, **kwargs):
        return " ".join(w.pprint(**kwargs) for w in self.words)

    def __getitem__(self, i: int):
        return self.words[i]

    def __len__(self) -> int:
        return len(self.words)

    def __init__(self, index, words):
        self.index: int = index  # position
        self.words: List[Word] = words


class Word(Representable, Readable):
    def pprint(self, **kwargs):
        return self.text

    def __init__(self, index: int, text, normalized_text: str):
        self.index: int = index  # position in sentence
        self.text: str = text
        self.normalized_text: str = normalized_text
        self.pos_tag: Labeled = None  # set later by an enricher
        self.embedding = None
        self.to_represent = {"text", "normalized_text"}


class Span(Sequence, Representable, Readable, Numeric):
    def numerify(self, *args, **kwargs):
        return self.embedding

    def __len__(self) -> int:
        return len(self.words)

    def __getitem__(self, i: int):
        return self.words[i]

    def pprint(self) -> str:
        return " ".join(w.pprint() for w in self.words)

    def __init__(self):
        self.words: List[Word] = None
        self.label: Labeled = None
        self.embedding = None

    def as_view(self, view):
        pass


class Link:
    def __init__(self, label, target):
        self.label: Labeled = label
        self.target = target
