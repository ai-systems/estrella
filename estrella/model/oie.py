from typing import List, Union, Dict, Type, Callable, Collection

from estrella.model.basic import Word, Span, Concept, Sentence, Document, Link
from estrella.interfaces import Representable, Readable, Viewable, Labeled
from estrella.util import pprint


class Fact(Concept):

    def __init__(self, id, sentence, context_level, simple_links=None,
                 fact_links=None):
        self.id = id
        self.sentence: Sentence = sentence

        self.context_level: int = context_level

        self.simple_links: List[ContextLink] = simple_links or []
        self.fact_links: List[ContextLink] = fact_links or []
        self._links = []

    @property
    def links(self):
        if not self._links == self.simple_links + self.fact_links:
            self._links = self.simple_links + self.fact_links
        return self._links


class SingleFact(Fact, Viewable):
    @classmethod
    def allowed_links(cls) -> Collection[str]:
        return "subject", "predicate", "object", "links"

    @classmethod
    def allowed_attributes(cls) -> Collection[str]:
        return "subject", "predicate", "object", "type", "text"

    @classmethod
    def creatable_from(cls) -> Dict[Type, Union[str, Callable]]:
        return {
            Document: "facts"
        }

    def __init__(self, id, sentence, context_level, subject, predicate, object, extraction_type, simple_links=None,
                 fact_links=None):
        super().__init__(id, sentence, context_level, simple_links, fact_links)
        self.subject: MaybeSpan = subject
        self.predicate: MaybeSpan = predicate
        self.object: MaybeSpan = object
        self.type = extraction_type

    def pprint(self, as_text=True) -> str:
        links = []
        spo_char = "─"
        if self.links:
            spo_char = "┬"
            links = [6 * " " + "├{}".format(pprint(link, as_text=as_text)) for link in self.links[:-1]]
            links.append(6 * " " + "└{}".format(pprint(self.links[-1], as_text=as_text)))
        spo = "{:>6}{}({})".format("[{}]".format(self.id), spo_char,
                                   pprint(self.subject, self.predicate, self.object, delimiter=")─("))
        return "\n".join([spo, "\n".join(links)])

    @property
    def text(self):
        return " ".join((self.subject.text, self.predicate.text, self.object.text))


class FactCollection(Fact):
    def pprint(self) -> str:
        return pprint(*self.facts, delimiter="\n")

    def __init__(self, id, facts: List[Fact], simple_links=None, fact_links=None):
        assert facts
        self.facts: List[Fact] = facts
        context_level = facts[0].context_level  # all facts in list are on same context level
        sentence = facts[0].sentence  # and in the same sentence
        super().__init__(id, sentence, context_level, simple_links, fact_links)


class MaybeSpan(Concept, Viewable):
    @classmethod
    def allowed_attributes(cls) -> Collection[str]:
        return "text",

    @classmethod
    def allowed_links(cls) -> Collection[str]:
        return []

    @classmethod
    def creatable_from(cls) -> Dict[Type, Union[str, Callable]]:
        return {}

    # TODO: this is going to be SpanOrLabel at some point
    def __init__(self, original_text, words=None):
        super().__init__()
        self.orig_text: str = original_text
        self.words: List[Word] = words or []

    def pprint(self, **kwargs):
        if self.words:
            return Span.pprint(self)
        return self.orig_text

    @property
    def text(self):
        return self.orig_text


class FactLabel(Labeled):
    NounBased = "NOUN_BASED"
    VerbBased = "VERB_BASED"
    Unknown = "UNKNOWN"


class ContextLabel(Labeled):
    Unknown = "UNKNOWN", "UNKNOWN_COORDINATION", "UNKNOWN_SUBORDINATION"

    # Coordinations
    # UnknownCoordination = "UNKNOWN_COORDINATION"  # the default for coordination
    Contrast = "CONTRAST"
    List = "LIST"
    Disjunction = "DISJUNCTION"

    # Subordinations
    # UnknownSubordination = "UNKNOWN_SUBORDINATION"  # the default for subordination
    Attribution = "ATTRIBUTION"
    Background = "BACKGROUND"
    Cause = "CAUSE", "CAUSE_C"
    Result = "RESULT", "RESULT_C"
    Condition = "CONDITION"
    Elaboration = "ELABORATION"
    Purpose = "PURPOSE"
    TemporalAfter = "TEMPORAL_AFTER", "TEMPORAL_AFTER_C"
    TemporalBefore = "TEMPORAL_BEFORE", "TEMPORAL_BEFORE_C"

    # for sentence simplification
    NounBased = "NOUN_BASED"
    Spatial = "SPATIAL"
    Temporal = "TEMPORAL", "TEMPORAL_TIME", "TEMPORAL_DURATION", "TEMPORAL_DATE", "TEMPORAL_SET"

    # TemporalTime = "TEMPORAL_TIME"  # indicating a particular instance on a time scale (e.g. “Next Sunday 2 pm”).
    # TemporalDuration = "TEMPORAL_DURATION"
    # the amount of time between the two end-points of a time interval (e.g. “2 weeks").
    # TemporalDate = "TEMPORAL_DATE"  # particular date (e.g. “On 7 April 2013”).
    # TemporalSet = "TEMPORAL_SET"
    # periodic temporal sets representing times that occur with some frequency (“Every Tuesday”).

    @classmethod
    def from_string(cls, string: str):
        for member in cls:
            if string in member.value:
                return member
        raise ValueError("No matching ContextLabel for {}".format(string))

    @classmethod
    def _inverse_map(cls):
        return {
            ContextLabel.Cause: ContextLabel.Result,
            ContextLabel.Result: ContextLabel.Cause
        }

    @property
    def inverse(self):
        return self._inverse_map().get(self, None)


class ContextLink(Link, Representable, Readable):
    def __init__(self, source: Fact, label: Union[ContextLabel, str], target: Union[Fact, MaybeSpan]):
        label = ContextLabel.from_string(label) or Labeled
        super().__init__(label, target)
        self.source = source
        self.is_simple = isinstance(target, MaybeSpan)
        self.is_coordinate = source.context_level >= 0 and source.context_level == getattr(target, "context_level", -2)

    def pprint(self, as_text=True):
        if self.is_simple:
            target_str = "".join(("(", pprint(self.target), ")"))
        else:
            target_str = "".join(("[", str(self.target.id), "]")) if not as_text else "({})".format(
                pprint(self.target.subject,
                       self.target.predicate,
                       self.target.object,
                       delimiter=")─("))
        return "[{:^14}]─{}".format(self.label.name, target_str)
