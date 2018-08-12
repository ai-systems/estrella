from typing import List

from estrella.model.oie import FactLabel, Fact, ContextLabel

from estrella.util import pprint


def simple_print(facts_or_doc, as_text=True):
    facts = getattr(facts_or_doc, "facts", facts_or_doc)
    return "\n".join(pprint(fact, as_text=as_text) for fact in facts)


class HierarchicPrinter:
    id_indent = 5
    thread_indent_last = 13 * " "  # max(len(label) - 1
    thread_indent = "│" + 12 * " "  # max(len(label) - 2

    def __init__(self, as_text, facts):
        self.as_text = as_text
        self.facts = facts

    def format_fact(self, fact, simple, noun_based, coordinates, subordinates, context_level):
        lines = []
        formatted_fact = fact.pprint(deep=False)
        indent = (context_level * 4 + self.id_indent) * " "
        lines.extend(pprint("├", l, delimiter="") for l in simple)
        lines.extend(pprint("├", ContextLabel.NounBased, n, delimiter="") for n in noun_based)
        lines.extend(pprint("├", c, delimiter="", as_text=self.as_text) for c in coordinates)
        if not subordinates:
            lines[-1] = "└" + lines[-1][1:]
        else:
            for i, subordinate in enumerate(subordinates):
                subord_lines = self.format_fact(subordinate.target, *self.get(subordinate.target), context_level + 1)
                first_line = subord_lines[0]
                last = i == len(subordinates) - 1
                link_char = "└" if last else "├"
                subord_lines[0] = pprint(link_char, subordinate.label, first_line, delimiter="")
                label_indent = self.thread_indent_last if last else self.thread_indent
                subord_lines[1:] = ["".join((label_indent, l)) for l in subord_lines[1:]]
                lines.extend(subord_lines)

        if lines:
            formatted_fact = formatted_fact[:5] + "┬" + formatted_fact[6:]
        return [formatted_fact] + [indent + l for l in lines]

    def get_main_facts(self):
        return (fact for fact in self.facts if (fact.context_level <= 0 and fact.type != FactLabel.NounBased))

    def get(self, fact):
        simple_links = (l for l in fact.simple_links)
        noun_based = []
        coordinates = []
        subordinates = []
        for link in fact.fact_links:
            if link.label == ContextLabel.NounBased:
                noun_based.append(link.target)
            elif link.is_coordinate:
                coordinates.append(link)
            else:
                subordinates.append(link)
        return simple_links, noun_based, coordinates, subordinates

    def print(self):
        lines = []
        main_facts: List[Fact] = self.get_main_facts()
        for fact in main_facts:
            formatted_lines = self.format_fact(fact, *self.get(fact), 0)
            lines.extend(formatted_lines)
        return "\n".join(lines)


def hierarchic_print(facts_or_doc, as_text=True):
    facts = getattr(facts_or_doc, "facts", facts_or_doc)
    printer = HierarchicPrinter(as_text, facts)
    return printer.print()
