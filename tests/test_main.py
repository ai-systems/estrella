from estrella.main import Estrella
from estrella.model.oie import ContextLabel
from tests import testutil
from nose import tools as nt
from estrella.serialize.readable import oie as oie_serialize

cfg = testutil.setup_config_and_logging()


class MainTester:
    def test_successful_main(self):
        main = Estrella(cfg_or_path=cfg['main'])
        p = main.get_pipeline("test_pipeline")
        p.assemble()
        main.run_pipeline("test_pipeline", "tests/resources/test.txt")
        d = main.docs.filter(language=main.languages.English)
        doc = d.copy()[0]
        nt.assert_equal(len(d), 1)
        facts = d.hop("facts")
        vectors = [f.numerify() for f in facts]

        contexts = facts.filter(
            filter_predicate=lambda f: "intel" in f.subject.text.lower()
        ).hop(
            link_name="links", constraint=lambda link: link.label == ContextLabel.Background
        )
        nt.assert_equal(len(contexts), 1)
        l = main.dist_service.sort_by_relatedness("intel", doc.words, attr="normalized_text")
        nt.assert_equal(l[0].text, "Intel")
        nt.assert_equal(l[-1].text, "found")
