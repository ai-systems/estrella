from abc import ABCMeta, abstractmethod
from collections import defaultdict
from typing import Dict, Iterable

from estrella import util
from estrella.enrich import Enricher
from estrella.model.basic import Document

import numpy as np


def oov_embedding(seed, size):
    s = np.random.get_state()
    np.random.seed(seed)
    oov = np.random.rand(size)
    np.random.set_state(s)
    return oov


def zero_embedding(size):
    return [0] * size


class EmbeddingProvider(metaclass=ABCMeta):
    @abstractmethod
    def get_embeddings(self, strings: Iterable[str]) -> Dict[str, np.array]:
        pass


class EmbeddingEnricher(Enricher):
    def __init__(self, embedding_provider: EmbeddingProvider, random_seed=1337):
        super().__init__()
        self.rdm_seed = random_seed  # should be moved to one place at some point
        self.embedding_provider: EmbeddingProvider = util.safe_construct(embedding_provider,
                                                                         restrict_to=EmbeddingProvider,
                                                                         relative_import="estrella.operate.embedding")

    def enrich(self, document: Document):
        # possibly with cache
        vocab = set(word.normalized_text for word in document.words)
        embeddings = self.embedding_provider.get_embeddings(vocab)
        try:
            oov_size = len(next(emb for emb in embeddings.values() if emb))
        except StopIteration:
            raise ValueError("Document has not a single word with a known embedding!")
        oov_vector = oov_embedding(self.rdm_seed, oov_size)
        for word in document.words:
            word.embedding = np.array(embeddings[word.normalized_text] or oov_vector, dtype=np.float32)


class FactEmbeddingEnricher(Enricher):
    def __init__(self, embedding_provider: EmbeddingProvider, random_seed=1337):
        super().__init__()
        self.rdm_seed = random_seed  # should be moved to one place at some point
        self.embedding_provider: EmbeddingProvider = util.safe_construct(embedding_provider,
                                                                         restrict_to=EmbeddingProvider,
                                                                         relative_import="estrella.operate.embedding")

    def enrich(self, document: Document):
        if getattr(document, 'facts', False):
            text_to_span = defaultdict(list)
            for fact in document.facts:
                text_to_span[fact.subject.text].append(fact.subject)
                text_to_span[fact.predicate.text].append(fact.predicate)
                text_to_span[fact.object.text].append(fact.object)
                for l in fact.simple_links:
                    text_to_span[l.target.text].append(l.target)
            embeddings = self.embedding_provider.get_embeddings(k for k in text_to_span.keys() if k)

            try:
                embedding_size = len(next(emb for emb in embeddings.values() if emb))
            except StopIteration:
                raise ValueError("Document has not a single word with a known embedding!")

            if text_to_span.get('', None) is not None:
                embeddings[''] = zero_embedding(embedding_size)

            oov_vector = oov_embedding(self.rdm_seed, embedding_size)
            for k, v in text_to_span.items():
                for span in v:
                    span.embedding = np.array(embeddings[k] or oov_vector, dtype=np.float32)
