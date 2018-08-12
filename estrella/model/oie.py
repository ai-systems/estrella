from typing import List, Union, Dict, Type, Callable, Collection

from estrella.model.basic import Sentence, Document, Link
from estrella.interfaces import Representable, Readable, Viewable, Labeled, Numeric
from estrella.util import pprint


class Fact(Viewable, Representable, Readable, Numeric):
    def numerify(self, *args, **kwargs):
        return (self.id,
                self.subject.numerify(*args, **kwargs),
                self.predicate.numerify(*args, **kwargs),
                self.object.numerify(*args, **kwargs),
                [l.numerify(*args, **kwargs) for l in self.simple_links],
                [l.numerify(*args, **kwargs) for l in self.fact_links])

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

    @property
    def links(self):
        if not self._links == self.simple_links + self.fact_links:
            self._links = self.simple_links + self.fact_links
        return self._links

    def __init__(self, id, sentence, context_level, subject, predicate, object, extraction_type, simple_links=None,
                 fact_links=None):
        self.id = id
        self.sentence: Sentence = sentence

        self.context_level: int = context_level

        self.subject: MaybeSpan = subject
        self.predicate: MaybeSpan = predicate
        self.object: MaybeSpan = object

        self.simple_links: List[ContextLink] = simple_links or []
        self.fact_links: List[ContextLink] = fact_links or []

        self.type = extraction_type
        self._links = []

    def pprint(self, deep=True, **kwargs) -> str:
        links = []
        spo_char = "─"
        if self.links and deep:
            spo_char = "┬"
            links = [5 * " " + "├{}".format(pprint(link, **kwargs)) for link in self.links[:-1]]
            links.append(5 * " " + "└{}".format(pprint(self.links[-1], **kwargs)))
        spo = "─{:03d}─{}({})".format(self.id, spo_char,
                                      pprint(self.subject, self.predicate, self.object, delimiter=")─("))
        return "\n".join([spo, "\n".join(links)]) if links else spo

    @property
    def text(self):
        return " ".join((self.subject.text, self.predicate.text, self.object.text))


class MaybeSpan(Representable, Readable, Viewable, Numeric):
    # TODO: this will move in favor ov actual span

    def __init__(self, original_text):
        super().__init__()
        self.orig_text: str = original_text
        self.embedding = None

    def numerify(self, *args, **kwargs):
        return self.embedding

    @classmethod
    def allowed_attributes(cls) -> Collection[str]:
        return "text",

    @classmethod
    def allowed_links(cls) -> Collection[str]:
        return []

    @classmethod
    def creatable_from(cls) -> Dict[Type, Union[str, Callable]]:
        return {}

    def pprint(self, **kwargs):
        return self.orig_text

    @property
    def text(self):
        return self.orig_text


class FactLabel(Labeled):
    NounBased = "NOUN_BASED"
    VerbBased = "VERB_BASED"
    Unknown = "UNKNOWN"


class ContextLabel(Labeled):
    def pprint(self, **kwargs) -> str:
        return "[{:^14}]".format(self.name)

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


class ContextLink(Link, Representable, Readable, Numeric):

    def __init__(self, source: Fact, label: Union[ContextLabel, str], target: Union[Fact, MaybeSpan]):
        label = ContextLabel.from_string(label) or Labeled
        super().__init__(label, target)
        self.source = source
        self.is_simple = isinstance(target, MaybeSpan)
        self.is_coordinate = source.context_level >= 0 and source.context_level == getattr(target, "context_level", -2)

    def numerify(self, *args, **kwargs):
        if self.is_simple:
            return int(self.label), self.target.numerify(*args, **kwargs)
        else:
            return int(self.label), self.target.id

    def pprint(self, as_text=True, **kwargs):
        if self.is_simple:
            target_str = "".join(("(", pprint(self.target), ")"))
        else:
            target_str = "[{:03d}]".format(self.source.id) if not as_text else "({})".format(
                pprint(self.target.subject,
                       self.target.predicate,
                       self.target.object,
                       delimiter=")─("))
        return "{}─{}".format(pprint(self.label), target_str)
