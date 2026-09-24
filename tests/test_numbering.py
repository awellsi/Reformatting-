"""The numbering engine must agree with what the corpus meant to produce.

This is the check that makes the text-identity guarantee possible: if the
engine cannot say what a clause is called, nothing may rewrite it.
"""

import pytest
from docx import Document

from lfe.corpus import build, make_contract
from lfe.numbering import UnsupportedNumbering, _format_value, _to_letter, _to_roman, resolve


@pytest.mark.parametrize(
    ("value", "expected"),
    [(1, "i"), (2, "ii"), (4, "iv"), (9, "ix"), (14, "xiv"), (40, "xl"), (1990, "mcmxc")],
)
def test_roman_numerals(value: int, expected: str) -> None:
    assert _to_roman(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(1, "a"), (26, "z"), (27, "aa"), (28, "bb"), (52, "zz"), (53, "aaa")],
)
def test_word_repeats_letters_rather_than_counting_base_26(value: int, expected: str) -> None:
    assert _to_letter(value) == expected


def test_unsupported_format_is_refused_not_guessed() -> None:
    with pytest.raises(UnsupportedNumbering):
        _format_value(1, "chicago")


@pytest.mark.parametrize("seed", [1, 2, 3, 7, 11])
def test_resolved_labels_match_the_contract_model(tmp_path, seed: int) -> None:
    """Every number the model asked for is the number Word will render."""
    contract = make_contract(seed)
    path = build(contract, tmp_path / f"{seed}.docx")

    labels = resolve(Document(str(path)))
    assert len(labels) == len(contract.blocks)

    for label, block in zip(labels, contract.blocks, strict=True):
        assert label == block.number, f"{block.text[:40]!r}: rendered {label!r}"


def test_counters_reset_for_deeper_levels(tmp_path) -> None:
    """Clause 3's sub-clauses start at 3.1 again, not continue from clause 2."""
    contract = make_contract(1)
    path = build(contract, tmp_path / "reset.docx")
    labels = [label for label in resolve(Document(str(path))) if label]

    firsts = [label for label in labels if label.endswith(".1")]
    assert len(firsts) >= 2
    assert len(set(firsts)) == len(firsts)
