"""A four-level legal numbering definition: 1 / 1.1 / (a) / (i).

This is what a *correct* contract outline looks like in OOXML, and it is the
target the normaliser rebuilds towards (M3). The corpus needs it so that the
clean baseline documents are genuinely well-formed, not merely less ugly.

The ids sit well above anything in python-docx's default template (which uses
abstractNumId 0-8 and numId 1-9) so nothing collides.
"""

from __future__ import annotations

from docx.document import Document as DocumentT
from docx.oxml.ns import qn
from lxml import etree

ABSTRACT_NUM_ID = 100
NUM_ID = 100

# (format, text, left indent in twips, hanging indent in twips)
LEVELS = [
    ("decimal", "%1", 720, 720),
    ("decimal", "%1.%2", 1440, 720),
    ("lowerLetter", "(%3)", 2160, 720),
    ("lowerRoman", "(%4)", 2880, 720),
]


def _abstract_num() -> etree._Element:
    abstract = etree.Element(qn("w:abstractNum"))
    abstract.set(qn("w:abstractNumId"), str(ABSTRACT_NUM_ID))

    multi = etree.SubElement(abstract, qn("w:multiLevelType"))
    multi.set(qn("w:val"), "hybridMultilevel")

    for index, (fmt, text, left, hanging) in enumerate(LEVELS):
        lvl = etree.SubElement(abstract, qn("w:lvl"))
        lvl.set(qn("w:ilvl"), str(index))

        start = etree.SubElement(lvl, qn("w:start"))
        start.set(qn("w:val"), "1")

        num_fmt = etree.SubElement(lvl, qn("w:numFmt"))
        num_fmt.set(qn("w:val"), fmt)

        lvl_text = etree.SubElement(lvl, qn("w:lvlText"))
        lvl_text.set(qn("w:val"), text)

        justify = etree.SubElement(lvl, qn("w:lvlJc"))
        justify.set(qn("w:val"), "left")

        p_pr = etree.SubElement(lvl, qn("w:pPr"))
        ind = etree.SubElement(p_pr, qn("w:ind"))
        ind.set(qn("w:left"), str(left))
        ind.set(qn("w:hanging"), str(hanging))

    return abstract


def install(document: DocumentT) -> int:
    """Add the legal numbering definition to `document`; return its numId.

    Idempotent: installing twice leaves one definition.
    """
    numbering = document.part.numbering_part.element

    for existing in numbering.findall(qn("w:num")):
        if existing.get(qn("w:numId")) == str(NUM_ID):
            return NUM_ID

    abstract = _abstract_num()
    # w:abstractNum elements must precede every w:num in the part.
    last_abstract = numbering.findall(qn("w:abstractNum"))[-1]
    last_abstract.addnext(abstract)

    num = etree.SubElement(numbering, qn("w:num"))
    num.set(qn("w:numId"), str(NUM_ID))
    ref = etree.SubElement(num, qn("w:abstractNumId"))
    ref.set(qn("w:val"), str(ABSTRACT_NUM_ID))

    return NUM_ID


def apply(paragraph, num_id: int, level: int) -> None:
    """Attach paragraph to numbering instance `num_id` at outline `level` (1-based)."""
    p_pr = paragraph._p.get_or_add_pPr()
    num_pr = etree.SubElement(p_pr, qn("w:numPr"))

    ilvl = etree.SubElement(num_pr, qn("w:ilvl"))
    ilvl.set(qn("w:val"), str(level - 1))

    num = etree.SubElement(num_pr, qn("w:numId"))
    num.set(qn("w:val"), str(num_id))
