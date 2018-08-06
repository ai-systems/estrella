from pyhocon import ConfigTree

import estrella.interfaces
from estrella.model.basic import Document
import estrella.model
from estrella import util

from estrella.enrich import Enricher
from estrella.model import language
from estrella.model.language import Lang


class StaticDocumentEnricher(Enricher):

    def __init__(self, meta_tags, lang_config):
        super().__init__()
        self.meta_tags = meta_tags
        self.languages: Lang = language.from_config(lang_config)

    def _convert(self, k, v):
        if isinstance(v, ConfigTree):
            # if v is ConfigTree, then it's sth like k: {class: Label: args: Name}
            cls_name, kwargs = util.get_constructor_and_args(v)
            v = util.construct_from_config(cls_name, restrict_to=estrella.interfaces.Labeled,
                                           relative_import="estrella.model.labels")
        elif k == "language":
            v = self.languages.from_string(v)
        return k, v

    def enrich(self, document: Document):
        for k, v in self.meta_tags.items():
            attribute_exists = getattr(document, k, False)
            if attribute_exists is False:
                self.logger.warn("Setting non-defined attribute. Not an error, just a warning.")
            setattr(document, *self._convert(k, v))
