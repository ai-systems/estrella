from estrella.util import pprint


def simple_print(facts_or_doc, as_text=True):
    facts = getattr(facts_or_doc, "facts", facts_or_doc)
    return "\n".join(pprint(fact, as_text=as_text) for fact in facts)
