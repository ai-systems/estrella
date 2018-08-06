from estrella import pipeline, util
from nose import tools as nt


def setup_module():
    util.setup_logging("config/logging_tests.json")


class TestPipeline:
    @classmethod
    def setup_class(cls):
        cls.cfg = util.read_config("config/testing.conf")
        cls.tp = cls.cfg.test_pipeline
        print(util.format_config(cls.cfg))

    def test_successful_setup_from_config(self):
        pipeline.from_config(self.tp).assemble()

    def test_successful_setup_from_config_flat_kwargs(self):
        p = pipeline.from_config(self.tp)
        p.assemble(ending=".jpg")
        nt.assert_equal(p.source_reader.ending, ".jpg")

    def test_successful_parse_raw_text(self):
        p = pipeline.from_config(self.tp)
        p.assemble(ending=None)
        docs = p.load("tests/resources/test.txt")
        nt.assert_equal(len(docs), 1)
        doc = docs[0]
        nt.assert_equal(doc.language.name, "English")
        nt.assert_equal(doc.marco, "polo")
        nt.assert_equal(len(doc.sentences), 3)

        nt.assert_equal(doc.sentences[0].words[1].normalized_text, "corporation")
