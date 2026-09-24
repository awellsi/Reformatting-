"""The guarantee in docs/text-identity.md, exercised end to end.

The NUM-001 variant of a contract has its clause numbers typed into the text;
the clean variant generates them from numbering.xml. The two documents store
different characters and read identically -- which is exactly the case the
guarantee has to get right.
"""

import pytest

from lfe.corpus import build, make_contract
from lfe.corpus.build import NUM_001
from lfe.text import rendered_paragraphs, stored_paragraphs
from lfe.verify import NumberRemoval, check_claim, normalise, verify


@pytest.fixture
def variants(tmp_path):
    contract = make_contract(1)
    ugly = build(contract, tmp_path / "ugly.docx", defects=frozenset({NUM_001}))
    clean = build(contract, tmp_path / "clean.docx")
    return contract, ugly, clean


def test_the_two_variants_really_do_store_different_text(variants) -> None:
    _, ugly, clean = variants
    assert stored_paragraphs(ugly) != stored_paragraphs(clean)


def test_but_they_read_identically(variants) -> None:
    _, ugly, clean = variants
    assert rendered_paragraphs(ugly) == rendered_paragraphs(clean)


def test_typed_numbers_are_in_the_ugly_text_and_not_the_clean_one(variants) -> None:
    contract, ugly, clean = variants
    numbered = [b for b in contract.blocks if b.number is not None]
    ugly_text = stored_paragraphs(ugly)
    clean_text = stored_paragraphs(clean)

    for block in numbered:
        assert any(line.startswith(f"{block.number} ") for line in ugly_text)
    for block in numbered:
        assert not any(line.startswith(f"{block.number} ") for line in clean_text)


def _honest_claims(contract) -> list[NumberRemoval]:
    return [
        NumberRemoval(index=i, removed=block.number)
        for i, block in enumerate(contract.blocks)
        if block.number is not None
    ]


def test_a_fix_with_honest_claims_verifies(variants) -> None:
    contract, ugly, clean = variants
    result = verify(ugly, clean, claims=_honest_claims(contract))
    assert result.ok, result.describe()


def test_unclaimed_changes_are_rejected(variants) -> None:
    """The same fix, with nothing declaring it, must fail."""
    _, ugly, clean = variants
    result = verify(ugly, clean, claims=[])
    assert not result.ok
    assert result.unattributed


def test_a_claim_that_does_not_match_the_generated_label_is_rejected(variants) -> None:
    """Deleting '2.1' from a clause that will render '2.2' must fail."""
    contract, ugly, clean = variants
    claims = _honest_claims(contract)
    poisoned = [
        NumberRemoval(index=c.index, removed="9.9") if i == 0 else c for i, c in enumerate(claims)
    ]
    result = verify(ugly, clean, claims=poisoned)
    assert not result.ok
    assert result.rejected_claims or result.unattributed


def test_real_content_edits_are_caught_even_with_claims(tmp_path) -> None:
    """A smuggled word change fails reader identity, claims notwithstanding."""
    contract = make_contract(2)
    ugly = build(contract, tmp_path / "u.docx", defects=frozenset({NUM_001}))

    tampered = make_contract(2)
    body = next(i for i, b in enumerate(tampered.blocks) if b.text.startswith("The Supplier shall"))
    tampered.blocks[body] = type(tampered.blocks[body])(
        kind=tampered.blocks[body].kind,
        text=tampered.blocks[body].text.replace("shall", "may"),
        level=tampered.blocks[body].level,
        number=tampered.blocks[body].number,
    )
    edited = build(tampered, tmp_path / "e.docx")

    result = verify(ugly, edited, claims=_honest_claims(contract))
    assert not result.ok
    assert result.reader_differences


def test_normalise_collapses_whitespace_only() -> None:
    assert normalise("a\t b\n c ") == "a b c"
    assert normalise("2.1  The Supplier") == "2.1 The Supplier"


class TestCheckClaim:
    """The claim check, exercised directly rather than through documents.

    Some of these states cannot arise while reader identity also holds; they are
    checked here so the function stays correct if that ever changes.
    """

    def test_an_honest_removal_is_accepted(self) -> None:
        assert (
            check_claim("2.1 The Supplier shall pay.", "The Supplier shall pay.", "2.1", "2.1")
            is None
        )

    def test_whitespace_differences_do_not_matter(self) -> None:
        assert (
            check_claim("2.1\tThe Supplier shall pay.", "The Supplier  shall pay.", "2.1", "2.1")
            is None
        )

    def test_taking_a_word_with_the_number_is_rejected(self) -> None:
        reason = check_claim("2.1 The Supplier shall pay.", "Supplier shall pay.", "2.1", "2.1")
        assert reason is not None
        assert "does not give this text" in reason

    def test_removing_a_number_that_was_not_there_is_rejected(self) -> None:
        assert (
            check_claim("The Supplier shall pay.", "The Supplier shall pay.", "2.1", "9.9")
            is not None
        )

    def test_a_paragraph_that_generates_nothing_is_rejected(self) -> None:
        reason = check_claim("2.1 The Supplier shall pay.", "The Supplier shall pay.", None, "2.1")
        assert reason is not None
        assert "generates no number" in reason

    def test_a_label_that_differs_from_what_was_removed_is_rejected(self) -> None:
        """The heart of it: delete '2.1' from a clause that renders '2.2'."""
        reason = check_claim("2.1 The Supplier shall pay.", "The Supplier shall pay.", "2.2", "2.1")
        assert reason is not None
        assert "generates '2.2'" in reason
