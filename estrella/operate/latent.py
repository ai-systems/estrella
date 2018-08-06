import json
from abc import ABCMeta, abstractmethod
from operator import attrgetter
from typing import Sequence, Collection, List, Dict

import requests

from estrella.enrich.latent import EmbeddingProvider


class EmbeddingComparator(metaclass=ABCMeta):
    @abstractmethod
    def sort_by_relatedness(self, compare_with: str, comparables: Sequence, attr: str = None):
        """
        This method is supposed to sort a sequence of strings (or objects containing string) by their distance to a
        given string.

        :param compare_with: String to compare the distance to.
        :param comparables: List of objects to be sorted.
        :param attr: Name of attribute to get the string from. If not supplied, it is assumed `comparables` is a
        sequence of strings.
        :return: `comparables` sorted by their semantic relatedness to a given string.
        """
        pass


class Indra(EmbeddingComparator, EmbeddingProvider):
    """
    Stub class to make http request to the Indra distributed semantics service.
    """

    def __init__(self, corpus="googlenews", model="W2V", language="EN", server="localhost", scoring_function='COSINE',
                 port=8916):
        self.corpus = corpus
        self.model = model
        self.language = getattr(language, "value", False) or language
        self.relatedness_endpoint = "http://{}:{}/relatedness".format(server, port)
        self.scoring_function = scoring_function
        self.embeddings_endpoint = "http://{}:{}/vectors".format(server, port)

    def get_embeddings(self, strings: Collection[str]) -> Dict[str, float]:
        """
        Embeds the words in the configured vector space and returns the embeddings. Returns None for word where
        the embedding is not known.

        :param strings: Words to embed.
        :return: Mapping between the given words and their embedding in the configured vector space. For every word that
        has no embedding in the vector space, returns None.
        """
        payload = {
            'corpus': self.corpus,
            'model': self.model,
            'language': self.language,
            'terms': list(strings)
        }
        headers = {
            'content-type': "application/json"
        }
        response = requests.request("POST", self.embeddings_endpoint, data=json.dumps(payload), headers=headers)

        response.raise_for_status()

        response = response.json()['terms']
        return response

    def get_semantic_relatedness(self, pairs):
        """
        Calls the indra endpoint to obtain pair-wise relatedness for a list of pairs.

        :param pairs: list of word pairs where each element looks like {"t1": word1, "t2": word2}
        :return: list of word pairs where each element looks like {"t1": word1, "t2": word2, "score": value}
        """
        payload = {
            'corpus': self.corpus,
            'model': self.model,
            'language': self.language,
            'scoreFunction': self.scoring_function,
            'pairs': pairs
        }
        headers = {
            'content-type': "application/json"
        }
        response = requests.request("POST", self.relatedness_endpoint, data=json.dumps(payload), headers=headers)

        response.raise_for_status()

        response = response.json()['pairs']
        return response

    def sort_by_relatedness_with_id(self, comparator, comparables, id_name="_id", format="{name}"):
        """
        Sorts a list of dictionaries by their relatedness to a given input.
        Which fields of a dictionary to use for comparison can be defined via the keyword argument 'format' using
        python's new style formatting, which field to take as id via 'id_name'.

        :param comparator: Plain text to compare the list to.
        :type comparator: str
        :param comparables: List of dictionaries to sort.
        :type comparables: list
        :param id_name: Key name of a single dict entry. Defaults to "_id".
        :type id_name: str
        :param format: String format template which defines which dict entries and in which order to use for comparison. Defaults to "_name"
        :type format: str
        :return: List of entries sorted by their semantic relatedness to word.
        :rtype: list
        """
        pairs = [{"t1": comparator,
                  "t2": ("{id} | " + format).format(
                      id=words_dict[id_name], **{k: v for k, v in words_dict.items() if not k == id_name})}
                 for words_dict in comparables]
        result = sorted(self.get_semantic_relatedness(pairs), reverse=True, key=lambda x: x['score'])
        return [entry["t2"].split(" | ", 1)[0] for entry in result]

    def sort_by_relatedness(self, compare_with: str, comparables: Sequence, attr: str = None):
        """
        Sorts a list of objects by their relatedness to a given plain text.
        The object's representation function can also be defined as well as specific arguments which have to be used with
        that function.

        :param compare_with: string to compare to.
        :param comparables: list of objects to sort.
        :param attr: Name of attribute to get the string from. If not supplied,
            assuming comparables is a sequence of strings.
        :return: List of objects sorted by their semantic relatedness.
        :rtype: list
        """
        get = attrgetter(attr) if attr else lambda x: x
        words_with_ids = [
            {
                "_id": id,
                "name": get(comparable)
            }
            for id, comparable in enumerate(comparables)]
        result = self.sort_by_relatedness_with_id(compare_with, words_with_ids)

        return [comparables[int(id)] for id in result]
