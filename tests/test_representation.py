from estrella.input.format.raw_text import RawTextReader
from estrella.input.normalizers import DefaultNormalizer
from estrella.serialize.readable import oie as oie_serialize
from tests import testutil
from nose import tools as nt

cfg = testutil.setup_config_and_logging()


class TestPrettyPrinter:
    def test_pretty_print(self):
        example = ["Franz jagt im komplett verwahrlosten Taxi quer durch Bayern."]
        doc = RawTextReader(normalizer=DefaultNormalizer()).read_resource(example)[0]
        nt.assert_equal(doc.pprint(), "Franz jagt im komplett verwahrlosten Taxi quer durch Bayern .")

    def test_pretty_print_facts_simple(self):
        doc = testutil.fake_extract_graphene(1)
        print()
        print(oie_serialize.simple_print(doc, as_text=True))
        print(20 * "-")
        print(oie_serialize.simple_print(doc, as_text=False))
        print(20 * "-")
        print(oie_serialize.hierarchic_print(doc, as_text=False))
