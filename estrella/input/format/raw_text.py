from estrella.input.format import FormatReader
from estrella.model.basic import Word, Sentence, Document
from nltk.tokenize import word_tokenize, sent_tokenize


class RawTextReader(FormatReader):
    def __init__(self, normalizer, keep_original_text=True):
        super().__init__(normalizer)
        self.keep_original_text = keep_original_text

    def create_doc(self, loaded_resource: str) -> Document:
        loaded_resource = self.normalizer.normalize(loaded_resource)
        doc = Document([
            Sentence(
                index, ([
                    Word(i, word, self.normalizer.normalize_word(word))
                    for i, word in enumerate(word_tokenize(sent))
                ])
            )

            for index, sent in enumerate(sent_tokenize(loaded_resource))
        ])
        doc._text = loaded_resource if self.keep_original_text else self.normalizer.revert(doc)
        return doc
