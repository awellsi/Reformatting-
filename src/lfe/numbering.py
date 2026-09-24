"""Resolving OOXML numbering to the labels a reader actually sees.

Word does not store "2.1" anywhere in document.xml. It stores a pointer to a
numbering instance and an outline level, and computes the label at render time
by walking the document and keeping a counter per level. To know what a clause
is *called*, that walk has to be reproduced.

This module is load-bearing for the text-identity guarantee (see
docs/text-identity.md): a typed number may only be removed when the label
generated in its place is character-for-character the same string.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from docx.document import Document as DocumentT
from docx.oxml.ns import qn
from lxml import etree

PLACEHOLDER = re.compile(r"%([1-9])")

# Formats that appear in legal documents. Anything outside this set is reported
# rather than guessed at -- see `Level.render`.
SUPPORTED_FORMATS = frozenset(
    {"decimal", "lowerLetter", "upperLetter", "lowerRoman", "upperRoman", "none"}
)

ROMAN = [
    (1000, "m"),
    (900, "cm"),
    (500, "d"),
    (400, "cd"),
    (100, "c"),
    (90, "xc"),
    (50, "l"),
    (40, "xl"),
    (10, "x"),
    (9, "ix"),
    (5, "v"),
    (4, "iv"),
    (1, "i"),
]


class UnsupportedNumbering(Exception):
    """A numbering construct this engine will not guess at."""


def _to_roman(value: int) -> str:
    if value <= 0:
        raise UnsupportedNumbering(f"roman numeral for {value}")
    out = []
    for amount, numeral in ROMAN:
        while value >= amount:
            out.append(numeral)
            value -= amount
    return "".join(out)


def _to_letter(value: int) -> str:
    """1 -> a, 26 -> z, 27 -> aa, matching Word's repetition (not base-26)."""
    if value <= 0:
        raise UnsupportedNumbering(f"letter for {value}")
    index = (value - 1) % 26
    repeats = (value - 1) // 26 + 1
    return chr(ord("a") + index) * repeats


@dataclass(frozen=True)
class Level:
    ilvl: int
    start: int
    num_fmt: str
    lvl_text: str
    lvl_restart: int | None
    is_lgl: bool


def _format_value(value: int, num_fmt: str) -> str:
    if num_fmt == "decimal":
        return str(value)
    if num_fmt == "lowerLetter":
        return _to_letter(value)
    if num_fmt == "upperLetter":
        return _to_letter(value).upper()
    if num_fmt == "lowerRoman":
        return _to_roman(value)
    if num_fmt == "upperRoman":
        return _to_roman(value).upper()
    if num_fmt == "none":
        return ""
    raise UnsupportedNumbering(num_fmt)


@dataclass
class AbstractNum:
    abstract_id: int
    levels: dict[int, Level] = field(default_factory=dict)

    def render(self, ilvl: int, counters: dict[int, int]) -> str:
        """The label for level `ilvl` given the current counter per level.

        Each %n placeholder names a level, and is rendered in *that* level's
        own format -- so "%1.%2" under a decimal level 0 and a lowerLetter
        level 1 gives "2.b", not "2.2". w:isLgl on the rendering level forces
        every placeholder to decimal, which is what it is for.
        """
        level = self.levels[ilvl]

        def substitute(match: re.Match[str]) -> str:
            named = int(match.group(1)) - 1
            value = counters.get(named, 0)
            if level.is_lgl:
                return _format_value(value, "decimal")
            owner = self.levels.get(named)
            return _format_value(value, owner.num_fmt if owner else level.num_fmt)

        return PLACEHOLDER.sub(substitute, level.lvl_text)


@dataclass
class NumInstance:
    num_id: int
    abstract: AbstractNum
    start_overrides: dict[int, int] = field(default_factory=dict)

    def start_for(self, ilvl: int) -> int:
        if ilvl in self.start_overrides:
            return self.start_overrides[ilvl]
        level = self.abstract.levels.get(ilvl)
        return level.start if level else 1


def _int(element: etree._Element | None, attr: str = "w:val") -> int | None:
    if element is None:
        return None
    raw = element.get(qn(attr))
    return int(raw) if raw is not None else None


def _parse_level(node: etree._Element) -> Level:
    ilvl = int(node.get(qn("w:ilvl")))
    num_fmt_node = node.find(qn("w:numFmt"))
    lvl_text_node = node.find(qn("w:lvlText"))
    is_lgl_node = node.find(qn("w:isLgl"))

    return Level(
        ilvl=ilvl,
        start=_int(node.find(qn("w:start"))) or 1,
        num_fmt=(num_fmt_node.get(qn("w:val")) if num_fmt_node is not None else "decimal"),
        lvl_text=(lvl_text_node.get(qn("w:val")) if lvl_text_node is not None else ""),
        lvl_restart=_int(node.find(qn("w:lvlRestart"))),
        is_lgl=is_lgl_node is not None,
    )


@dataclass
class Numbering:
    """Every numbering definition in a document, ready to resolve against."""

    instances: dict[int, NumInstance] = field(default_factory=dict)

    @classmethod
    def from_document(cls, document: DocumentT) -> Numbering:
        try:
            part = document.part.numbering_part
        except (KeyError, AttributeError, ValueError):
            return cls()

        root = part.element
        abstracts: dict[int, AbstractNum] = {}
        for node in root.findall(qn("w:abstractNum")):
            abstract_id = int(node.get(qn("w:abstractNumId")))
            abstract = AbstractNum(abstract_id)
            for lvl in node.findall(qn("w:lvl")):
                level = _parse_level(lvl)
                abstract.levels[level.ilvl] = level
            abstracts[abstract_id] = abstract

        instances: dict[int, NumInstance] = {}
        for node in root.findall(qn("w:num")):
            num_id = int(node.get(qn("w:numId")))
            ref = node.find(qn("w:abstractNumId"))
            abstract_id = _int(ref)
            if abstract_id is None or abstract_id not in abstracts:
                continue
            instance = NumInstance(num_id, abstracts[abstract_id])
            for override in node.findall(qn("w:lvlOverride")):
                ilvl = int(override.get(qn("w:ilvl")))
                start_override = _int(override.find(qn("w:startOverride")))
                if start_override is not None:
                    instance.start_overrides[ilvl] = start_override
            instances[num_id] = instance

        return cls(instances)


def paragraph_numbering(paragraph: etree._Element) -> tuple[int, int] | None:
    """(numId, ilvl) for a paragraph, or None when it is not numbered."""
    num_pr = paragraph.find(qn("w:pPr") + "/" + qn("w:numPr"))
    if num_pr is None:
        return None
    num_id = _int(num_pr.find(qn("w:numId")))
    if num_id is None or num_id == 0:
        return None
    ilvl = _int(num_pr.find(qn("w:ilvl"))) or 0
    return num_id, ilvl


def resolve(document: DocumentT) -> list[str | None]:
    """The rendered label for each body paragraph, in order; None if unnumbered.

    Counters are kept per numbering instance, which is how Word behaves: two
    numIds pointing at the same abstractNum count independently.
    """
    numbering = Numbering.from_document(document)
    counters: dict[int, dict[int, int]] = {}
    labels: list[str | None] = []

    for paragraph in document.element.body.findall(qn("w:p")):
        target = paragraph_numbering(paragraph)
        if target is None:
            labels.append(None)
            continue

        num_id, ilvl = target
        instance = numbering.instances.get(num_id)
        level = instance.abstract.levels.get(ilvl) if instance else None
        if instance is None or level is None:
            labels.append(None)
            continue

        state = counters.setdefault(num_id, {})
        state[ilvl] = state.get(ilvl, instance.start_for(ilvl) - 1) + 1

        for deeper_ilvl, deeper in instance.abstract.levels.items():
            if deeper_ilvl > ilvl and deeper.lvl_restart != 0:
                state.pop(deeper_ilvl, None)

        visible = {
            other: state.get(other, instance.start_for(other))
            for other in instance.abstract.levels
            if other <= ilvl
        }
        labels.append(instance.abstract.render(ilvl, visible))

    return labels
