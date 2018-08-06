from abc import ABCMeta, abstractmethod
from typing import Collection, Dict

from estrella import util
from estrella.enrich import Enricher
from estrella.model.basic import Document

import numpy as np


class EmbeddingProvider(metaclass=ABCMeta):
    @abstractmethod
    def get_embeddings(self, strings: Collection[str]) -> Dict[str, np.array]:
        pass


class EmbeddingEnricher(Enricher):
    def __init__(self, embedding_provider: EmbeddingProvider, random_seed=1337):
        super().__init__()
        self.rdm_seed = random_seed  # should be moved to one place at some point
        self.embedding_provider: EmbeddingProvider = util.safe_construct(embedding_provider,
                                                                         restrict_to=EmbeddingProvider,
                                                                         relative_import="estrella.operate.latent")

    def oov_embedding(self, size):
        s = np.random.get_state()
        np.random.seed(self.rdm_seed)
        oov = np.random.rand(size)
        np.random.set_state(s)
        return oov

    def enrich(self, document: Document):
        # possibly with cache
        vocab = set(word.normalized_text for sentence in document for word in sentence)
        embeddings = self.embedding_provider.get_embeddings(vocab)
        try:
            oov_size = len(next(emb for emb in embeddings.values() if emb))
        except StopIteration:
            raise ValueError("Document has not a single word with a known embedding!")
        oov_vector = self.oov_embedding(oov_size)
        for word in document.words:
            word.embedding = np.array(embeddings[word.normalized_text] or oov_vector, dtype=np.float32)
