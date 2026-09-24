"""Reading text back out of a .docx.

Two different questions get asked of a document, and conflating them causes
trouble later:

- `stored_paragraphs` — the characters actually held in the XML. This is what
  the M3 text-identity verifier compares, because it is what an edit can
  silently change.
- Rendered text (numbers that Word generates from numbering definitions) is
  *not* stored anywhere in document.xml, so it cannot be read back here. The
  corpus tracks it separately, from the contract model that produced the file.
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.oxml.ns import qn


def stored_paragraphs(path: str | Path) -> list[str]:
    """Body paragraph text as stored in word/document.xml, in document order.

    Empty paragraphs are kept: a dropped blank line is still a change.
    """
    document = Document(str(path))
    body = document.element.body
    return ["".join(node.text or "" for node in p.iter(qn("w:t"))) for p in body.iter(qn("w:p"))]
