"""The source of truth for what a synthetic contract *says*.

A `Contract` is plain data: no formatting, no OOXML. The builder renders it to a
clean .docx; the defect injectors then corrupt the *presentation* of that same
text. Because both start from this model, the corpus always knows the exact body
text a document is supposed to contain, which is what makes text-identity
checking meaningful.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class BlockKind(Enum):
    TITLE = "title"
    HEADING = "heading"
    BODY = "body"
    DEFINITION = "definition"
    SCHEDULE_TITLE = "schedule_title"


@dataclass(frozen=True)
class Block:
    """One paragraph of the contract.

    `number` is the clause number as it should *display* (e.g. "2.1"). It is
    held separately from `text` so a defect injector can choose to type it into
    the text (NUM-001) or express it as real list numbering.
    """

    kind: BlockKind
    text: str
    level: int = 1
    number: str | None = None
    term: str | None = None

    def display_text(self) -> str:
        """The text a reader sees, number included."""
        if self.number is None:
            return self.text
        return f"{self.number} {self.text}"


@dataclass
class Contract:
    name: str
    blocks: list[Block] = field(default_factory=list)

    def text_lines(self) -> list[str]:
        """Every line of body text, in order, as a reader would see it."""
        return [b.display_text() for b in self.blocks]
