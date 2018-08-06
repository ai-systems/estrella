import json

from nose import tools as nt

from estrella.model.oie import Fact
from tests import testutil
from tests.testutil import setup_config_and_logging

from estrella.enrich.latent import EmbeddingEnricher
from estrella.input.format.raw_text import RawTextReader
from estrella.input.normalizers import DefaultNormalizer

import numpy as np

cfg = setup_config_and_logging()


class TestGrapheneEnricher:

    def test_successful_enrich(self):
        doc = testutil.fake_extract_graphene()
        nt.assert_equal(len(doc.facts), 2)
        first_fact: Fact = doc.facts[0]
        second_fact: Fact = doc.facts[1]
        nt.assert_equal(len(first_fact.fact_links), 1)
        nt.assert_equal(len(second_fact.fact_links), 0)


class TestIndraEnricher:
    def test_successful_embedding_enrich(self):
        enricher = EmbeddingEnricher(embedding_provider=cfg.indra_cfg)
        reader = RawTextReader(normalizer=DefaultNormalizer())
        doc = reader.read_resource(testutil.example)[0]
        enricher.enrich(doc)
        for word in doc.words:
            nt.assert_is_not_none(word.embedding)
        with open("resources/embeddings.json", "r") as f:
            embeddings = json.load(f)['terms']
        for i, word in enumerate(doc.words):
            if i > 5:
                break
            if word.normalized_text == ",":
                continue
            nt.assert_true((word.embedding == embeddings[word.normalized_text]).all())
        # , is oov
        s = np.random.get_state()
        comma = doc.words[2].embedding
        np.random.seed(enricher.rdm_seed)
        oov = np.array(np.random.rand(len(comma)), dtype=np.float32)
        np.random.set_state(s)
        nt.assert_true((comma == oov).all())
