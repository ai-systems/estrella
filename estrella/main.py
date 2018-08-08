from typing import Collection, Dict, Iterable

from pyhocon import ConfigTree

from estrella import util
from estrella.model import language
from estrella.model.basic import Document
from estrella.operate import view
from estrella.operate.latent import EmbeddingComparator
from estrella.operate.view import View
from estrella.pipeline import Pipeline, from_config
from estrella.interfaces import Loggable


class Estrella(Loggable):
    def __init__(self, cfg_path: str = None):
        super().__init__()
        self.cfg = util.read_config(cfg_path)['main']
        self._docs = []
        self.dist_service: EmbeddingComparator = util.safe_construct(self.cfg['embedding_comparator'],
                                                                     restrict_to=EmbeddingComparator,
                                                                     relative_import="estrella.operate.latent")
        self.languages = language.from_config(self.cfg['languages'])
        self.pipeline_configs: Dict[str, ConfigTree] = {
            k: v for k, v in self.cfg.get_config("pipelines").items()
        }  # from name to config
        self.pipelines: Dict[str, Pipeline] = {
            k: from_config(v) for k, v in self.pipeline_configs.items()
        }  # from name to actual pipeline

    def get_available_pipelines(self) -> Iterable[str]:
        """
        Returns all configured pipelines.

        :return: configured pipelines.
        """
        return self.pipelines.keys()

    def reset_pipeline(self, name):
        """
        Resets a pipeline given its name. (i.e. reloads it from config)

        Useful if you want to re-assemble it.

        :param name: Name of the pipeline to reset.
        :return: Newly created pipeline.
        """
        self.pipelines[name] = from_config(self.pipeline_configs[name])
        return self.pipelines[name]

    def get_pipeline(self, name: str) -> Pipeline:
        """
        Returns a pipeline given its name.

        :param name: Name of the pipeline.
        """
        return self.pipelines.get(name, None)

    def run_pipeline(self, name_or_pipeline, location, assemble=True):
        """
        Runs a given pipeline on a given location, adds the resulting documents to the document collection.

        :param name_or_pipeline: Name or actual pipeline to run.

        :param location: Initial resource to run the pipeline on.

        :param assemble: Whether to try to assemble without any arguments if not assembled yet.
        """
        p = self.pipelines[name_or_pipeline] if isinstance(name_or_pipeline, str) else name_or_pipeline
        if assemble and not p.assembled:
            p.assemble()
        docs = p.load(location)
        self.add_docs(docs)

    def add_docs(self, docs: Collection[Document]):
        """
        Adds a given collection of documents to the document collection.

        :param docs: Docs to be added.
        """
        for doc in docs:
            assert isinstance(doc, Document)
        self._docs.extend(docs)

    @property
    def docs(self) -> View[Document]:
        """
        Creates a view of all current documents.

        :return: View of all current documents.
        """
        return view.create_from(self, Document)
