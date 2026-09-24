"""Proving that a run changed only formatting.

The rule is stated in docs/text-identity.md. In short: the document must read
identically, and every change to stored text must be claimed by an edit
operation whose claim the engine can check.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from docx import Document

from .numbering import resolve
from .text import rendered_paragraphs, stored_paragraphs

WHITESPACE = re.compile(r"\s+")


def normalise(text: str) -> str:
    """Collapse runs of whitespace, so a tab-vs-space change is not a diff."""
    return WHITESPACE.sub(" ", text).strip()


@dataclass(frozen=True)
class NumberRemoval:
    """A claim that a typed number was deleted from a paragraph.

    `index` is the paragraph's position in the body, `removed` the exact string
    taken out. The claim is only accepted if the paragraph now renders with that
    same string as its generated label.
    """

    index: int
    removed: str


def check_claim(before: str, after: str, label: str | None, removed: str) -> str | None:
    """Why a number-removal claim is not acceptable, or None if it is.

    Two things must hold. Deleting `removed` from the stored text must give back
    exactly what is now stored -- nothing else may have gone with it. And the
    label the document now generates in that position must be the very string
    that was deleted, so the reader sees the same characters as before.

    The second is implied by the first together with reader identity, and is
    checked anyway: it is three lines, and it is the sentence the guarantee
    actually makes.
    """
    if normalise(before.removeprefix(removed)) != normalise(after):
        return f"removing {removed!r} does not give this text"
    if label is None:
        return f"{removed!r} was removed but the paragraph generates no number"
    if normalise(label) != normalise(removed):
        return f"generates {label!r}, but {removed!r} was removed"
    return None


@dataclass
class Difference:
    index: int
    before: str
    after: str
    reason: str


@dataclass
class VerificationResult:
    ok: bool
    reader_differences: list[Difference] = field(default_factory=list)
    unattributed: list[Difference] = field(default_factory=list)
    rejected_claims: list[Difference] = field(default_factory=list)

    def describe(self) -> str:
        if self.ok:
            return "text identity holds"
        parts = []
        for label, items in (
            ("reader-visible text changed", self.reader_differences),
            ("stored text changed with nothing claiming it", self.unattributed),
            ("claimed change did not match the generated label", self.rejected_claims),
        ):
            if items:
                first = items[0]
                parts.append(
                    f"{label} ({len(items)}): paragraph {first.index} "
                    f"{first.before!r} -> {first.after!r} [{first.reason}]"
                )
        return "; ".join(parts)


def verify(
    before: str | Path,
    after: str | Path,
    claims: list[NumberRemoval] | None = None,
) -> VerificationResult:
    """Check both conditions of the guarantee and report every failure found."""
    claims = claims or []
    by_index = {claim.index: claim for claim in claims}

    reader_before = [normalise(line) for line in rendered_paragraphs(before)]
    reader_after = [normalise(line) for line in rendered_paragraphs(after)]
    stored_before = [normalise(line) for line in stored_paragraphs(before)]
    stored_after = [normalise(line) for line in stored_paragraphs(after)]
    labels_after = resolve(Document(str(after)))

    result = VerificationResult(ok=True)

    if len(reader_before) != len(reader_after):
        result.ok = False
        result.reader_differences.append(
            Difference(
                index=-1,
                before=f"{len(reader_before)} paragraphs",
                after=f"{len(reader_after)} paragraphs",
                reason="paragraph count changed",
            )
        )
        return result

    for index, (was, now) in enumerate(zip(reader_before, reader_after, strict=True)):
        if was != now:
            result.ok = False
            result.reader_differences.append(Difference(index, was, now, "rendered text differs"))

    for index, (was, now) in enumerate(zip(stored_before, stored_after, strict=True)):
        if was == now:
            continue
        claim = by_index.get(index)
        if claim is None:
            result.ok = False
            result.unattributed.append(Difference(index, was, now, "no operation claimed this"))
            continue

        reason = check_claim(was, now, labels_after[index], claim.removed)
        if reason is not None:
            result.ok = False
            result.rejected_claims.append(Difference(index, was, now, reason))

    return result
