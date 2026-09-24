# The text-identity guarantee

The product does one thing: reformatting. So the promise that nothing else
changed has to be provable, not merely intended.

## The problem

Word does not store generated clause numbers. A properly numbered clause holds
only the text — `The Supplier shall provide the Services.` — plus a pointer to a
numbering instance. The `2.1` a reader sees is computed at render time.

A badly made document has `2.1` *typed into the text*. Fixing that (rule
NUM-001) means deleting those characters and attaching real numbering. A naive
before/after comparison of stored text therefore reports a change on every
clause we fix, and the guarantee becomes noise.

Comparing only rendered text is not good enough either: it would let a genuine
edit slip through whenever the change happened to cancel out in rendering.

## The rule

A run passes verification when **both** hold:

1. **Reader identity.** The rendered text — generated numbers included, computed
   by `lfe.numbering.resolve` — is identical before and after, after whitespace
   normalisation. This is what a human would check by reading both documents.

2. **Attributed change.** Every difference in *stored* text is claimed by an
   edit operation, and the claim is verified: for a typed-number removal, the
   deleted string must equal, character for character, the label the new
   numbering generates in that paragraph's position.

We never accept a change because it "looks like a number". `2.1` may only be
deleted when the engine proves the paragraph now renders as exactly `2.1`.
Delete `2.1` from a paragraph that will render `2.2` and the run fails.

The two conditions overlap on purpose. Given reader identity, and given that
removing the claimed string reproduces the stored text exactly, the generated
label *must* equal the claimed string — so the label comparison in
`lfe.verify.check_claim` is implied rather than independent. It is checked
anyway: it costs three lines, it is the sentence the guarantee actually makes,
and it keeps the claim check correct on its own terms if condition 1 is ever
relaxed. `check_claim` is therefore tested directly, including states that
cannot arise while condition 1 holds.

What condition 2 adds that condition 1 cannot: a stored change that happens to
cancel out in rendering. Moving text into a numbering definition, for instance,
reads the same and is still an edit. Nothing unclaimed passes.

## When the engine cannot say

`lfe.numbering` raises `UnsupportedNumbering` rather than guessing at a format
it does not implement. Anything it cannot resolve is not eligible for an
automatic number fix: the finding is reported for a human, and the text is left
untouched. A paragraph we cannot reason about is never rewritten.

## Consequences

- The numbering engine is load-bearing. It is tested against the corpus, where
  the intended label of every clause is known independently of the .docx.
- Rules that would change stored text without a provable substitution are not
  auto-fixable, however tempting. XRF-002 (typed "clause 4.3" cross-references)
  falls in this category and is flag-only until it can meet condition 2.
