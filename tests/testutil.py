import json
import os

from estrella import util
from estrella.enrich.semantic import GrapheneEnricher
from estrella.input.format.raw_text import RawTextReader
from estrella.input.normalizers import DefaultNormalizer


def setup_config_and_logging():
    util.setup_logging("tests/config/logging_test.conf")

    cfg = util.read_config("tests/config/testing.conf")
    return cfg


example = [
    "FedEx Corporation , originally known as FDX Corporation , is "
    "an American global courier delivery services company headquartered in Memphis , Tennessee .",
    "During his summers , he , a lawyer , returned to Chicago , "
    "where he worked as an associate at the law firms of Sidley Austin in 1989 and Hopkins & Sutter in 1990 ."
]
example_map = {
    0: "scratch.json",
    1: "elaborate_example.json"
}


def fake_extract_graphene(idx):
    enricher = GrapheneEnricher()
    reader = RawTextReader(normalizer=DefaultNormalizer())

    def dummy(*args, **kwargs):
        with open(os.path.join("tests", "resources", example_map[idx]), "r") as f:
            return json.load(f)

    doc = reader.read_resource(example)[0]
    enricher.get_graphene_output = dummy
    enricher.enrich(doc)
    return doc
