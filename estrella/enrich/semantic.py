import json
from collections import namedtuple
from typing import Dict

import requests

from estrella.enrich import Enricher
from estrella.model.oie import MaybeSpan, FactLabel, ContextLink, Fact


def _get(serialized, *paths, as_cls=lambda x: x):
    if len(paths) == 1:
        return as_cls(serialized[paths[0]])
    return tuple(as_cls(serialized[path]) for path in paths)


class GrapheneEnricher(Enricher):
    def __init__(self, do_coreference=False, server_address="localhost", server_port=8080, group_lists=False):
        super().__init__()
        self.do_coreference = do_coreference
        self.server_address = server_address
        self.server_port = server_port
        self.server_address = server_address
        self.group_lists = group_lists

    def get_graphene_output(self, document) -> Dict:
        url = "http://{}:{}/relationExtraction/text".format(self.server_address, self.server_port)
        data = {
            'text': document.plaintext,
            'doCoreference': self.do_coreference,
            'isolateSentences': False,
            'format': "DEFAULT",
        }

        headers = {
            'content-type': "application/json",
            'Accept': "application/json"
        }

        response = requests.request("POST", url, data=json.dumps(data), headers=headers)

        try:
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(e, exc_info=True)

    # put into graphene stub and gather output
    # create facts, link LinkedContexts
    # first iteration: everything else is MaybeSpan
    # second iteration: try to link Subj/Obj, curate graphenes inability to split sentences correctly
    # first: only if only one exact match, then if partial & overlapping etc
    # third iteration: try to link simpleContexts
    # 4th phase: try to link predicate
    # create OIE spans (Facts)
    # be-a
    # be+gerund / be+participle
    # where/there
    # list
    def enrich(self, document):
        SLT = namedtuple("SLT", ("source", "label", "target"))

        serialized_facts = self.get_graphene_output(document)['extractions']
        facts = []

        id_to_fact = dict()
        fact_links = []  # map from fact to its contexts

        for simple_id, serialized_fact in enumerate(serialized_facts):
            long_id = serialized_fact["id"]
            # create basic fact
            fact = Fact(simple_id,  # id
                        document[serialized_fact['sentenceIdx']],  # sentence
                        serialized_fact['contextLayer'],  # context_level
                        *_get(serialized_fact, "arg1", "relation", "arg2", as_cls=MaybeSpan),  # spo
                        extraction_type=FactLabel.from_string(serialized_fact['type'])
                        )

            # save map from long id to fact
            id_to_fact[long_id] = fact

            # add simple links
            fact.simple_links = [
                ContextLink(
                    source=fact,
                    label=context['classification'],
                    target=MaybeSpan(context['text'])
                ) for context in serialized_fact['simpleContexts'] if context["classification"] != "NOUN_BASED"
            ]  # NOUN_BASED will be in linkedContexts anyways
            # prepare linked facts
            for context in serialized_fact['linkedContexts']:
                # source-label-target
                fact_links.append(SLT(fact, context['classification'], context['targetID']))
            facts.append(fact)

        # group lists
        if self.group_lists:
            facts = self.group_by_lists(facts, fact_links, id_to_fact)

        # handle linked facts
        for source, label, target in fact_links:
            source.fact_links.append(ContextLink(source=source, label=label, target=id_to_fact[target]))

        document.facts = facts


    def group_by_lists(self, facts, links, id_map):
        # create FactCollection for every list
        # for all fact_collections
        #  -> for all fact_links with same source (target) and all targets (sources) in collection
        #    -> change target (source) to collection
        # cleanup: remove grouped facts from facts and add fact_collections instead
        # cleanup: remove links with changed targets
        return facts
