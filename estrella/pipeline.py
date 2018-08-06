import logging
from collections import defaultdict
from enum import Enum, auto
from typing import List, Tuple, Type

import estrella.interfaces
from estrella.enrich import Enricher
from estrella.exceptions.pipeline import PipelineException
from estrella.input.format import FormatReader
from estrella.input.source import SourceReader
import inspect
from estrella import util


class Sources(Enum):
    Config = auto()
    Assembled = auto()
    Classes = auto()


def from_config(cfg):
    pipeline = Pipeline(Sources.Config)
    pipeline.config = cfg
    return pipeline


def from_instances(source_reader, format_reader, enrichers):
    pipeline = Pipeline(Sources.Assembled)
    pipeline.source_reader = source_reader
    pipeline.format_reader = format_reader
    pipeline.enrichers = enrichers


def from_classes(source_reader_cls, format_reader_cls, enricher_classes):
    pipeline = Pipeline(Sources.Classes)
    pipeline.source_reader_cls = source_reader_cls
    pipeline.format_reader_cls = format_reader_cls
    pipeline.enricher_classes = [(c, {}) for c in enricher_classes]


class Pipeline(estrella.interfaces.Loggable):
    def __init__(self, source):
        super().__init__()

        self.source = source
        self.assembled = False or self.source == Sources.Assembled

        self.config = None

        self.source_reader: SourceReader = None
        self.format_reader: FormatReader = None
        self.enrichers: List[Enricher] = []

        self._no_name_clashes = True
        self._arg_to_cls = dict()
        self._args_flat = set()
        self._args_deep = dict()

        self.enricher_classes: List[Tuple[Type[Enricher], dict]] = []
        self.source_reader_cls: Type[SourceReader] = None
        self.source_reader_args = dict()
        self.format_reader_cls: Type[FormatReader] = None
        self.format_reader_args = dict()

    def check_required_args(self, cls):
        params = inspect.signature(cls.__init__).parameters
        self._no_name_clashes = self._no_name_clashes and not self._args_flat.intersection(params.keys())
        self.logger.debug("No name clashes: {}".format(self._no_name_clashes))
        if self._no_name_clashes:
            self._args_flat = self._args_flat.union(set(params.keys()) - {"self"})
            for param_name in params.keys():
                self._arg_to_cls[param_name] = cls
        else:
            self.logger.debug(self._args_flat.intersection(params.keys()))
        self._args_deep[cls] = params

    def _from_cfg(self, cfg_path, restrict_to, relative_import):
        cls_name, kwargs = util.get_constructor_and_args(cfg_path)
        cls = util.load_class(cls_name, restrict_to, relative_import)
        self.check_required_args(cls)
        self.logger.debug("Loaded: {} {}".format(cls_name, kwargs))
        return cls, kwargs

    def assemble(self, **kwargs):
        if self.assembled:
            raise PipelineException("Cannot assemble an already assembled pipeline! "
                                    "Reasons: either constructed from classes or pipeline.assemble() already called.")
            # merge **kwargs with config as requested
        # 0) load corresponding classes
        # - SourceReader, FormatReader, Enrichers (more about that later)
        # 1) determine required parameters from functions
        # - SourceReader.__init__, FormatReader.__init__, for enricher in enrichers: __init__
        if self.source == Sources.Config:
            self.source_reader_cls, self.source_reader_args = self._from_cfg(self.config.source_reader,
                                                                             restrict_to=SourceReader,
                                                                             relative_import="estrella.input.source")

            self.format_reader_cls, self.format_reader_args = self._from_cfg(self.config.format_reader,
                                                                             restrict_to=FormatReader,
                                                                             relative_import="estrella.input.format")

            # same for enrichers
            for entry in self.config.enrichers:
                cls_name, cls_args = util.get_constructor_and_args(entry)
                cls = util.load_class(cls_name, restrict_to=Enricher, relative_import="estrella.enrich")
                self.check_required_args(cls)
                self.enricher_classes.append((cls, cls_args))

        elif self.source == Sources.Classes:
            if not kwargs.get('cls_dicts', None):
                raise PipelineException("If pipeline is constructed from classes, you need to provide the args"
                                        "to actually construct those classes.")
        # 2) check **kwargs:
        cls_dicts = defaultdict(dict)
        if kwargs:
            self.logger.debug("Merging kwargs with config...")
            # 2a) if no name clashes: simple strategy allowed -> required_args_flat
            if self._no_name_clashes:
                self.logger.debug("No name clashes, merging flat kwargs..")
                # put all existing args into corresponding dicts
                for param_name, param_val in kwargs.items():
                    param_cls = self._arg_to_cls[param_name]
                    cls_dicts[param_cls][param_name] = param_val
            else:
                # 2b) expect cls_dicts to be handed via cls_dicts
                # convert into default dict
                self.logger.debug("Expecting a cls_dicts....")
                for cls_key, cls_kwargs in kwargs.get('cls_dicts', dict()).items():
                    cls_dicts[cls_key] = cls_kwargs
        # 3) merge & construct, throw exception if sth is missing
        # since cls_dicts comes after source_reader_cls, cls_dicts overrides config values
        self.source_reader = util.construct(self.source_reader_cls,
                                            dict(self.source_reader_args, **cls_dicts[self.source_reader_cls]))
        self.format_reader = util.construct(self.format_reader_cls,
                                            dict(self.format_reader_args, **cls_dicts[self.format_reader_cls]))
        for enricher_cls, enricher_kwargs in self.enricher_classes:
            self.enrichers.append(util.construct(enricher_cls, dict(enricher_kwargs, **cls_dicts[enricher_cls])))
        self.assembled = True

    def load(self, location):
        if not self.assembled:
            raise PipelineException("Cannot run a pipeline that was not assembled yet!"
                                    "Run pipeline.assemble(**kwargs)!")
        res = self.source_reader.load(location)
        docs = self.format_reader.read_resource(res)
        # TODO make Parallel
        for document in docs:
            for enricher in self.enrichers:
                enricher.enrich(document)
        return docs
