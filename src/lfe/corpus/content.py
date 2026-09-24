"""Deterministic contract text.

The wording is unremarkable on purpose. What matters for the corpus is the
*shape*: nested clause numbering, defined terms that are used later, headings
at four levels, and a schedule — the structures the analyser has opinions about.
Every contract is built from a seed, so the corpus is reproducible.
"""

from __future__ import annotations

import random

from .model import Block, BlockKind, Contract

PARTIES = [
    ("Northgate Holdings Limited", "Alder Supply Co Limited"),
    ("Westrow Technologies Limited", "Pennine Logistics Limited"),
    ("Cavendish Marine Limited", "Harbourpoint Services Limited"),
    ("Silverbrook Estates Limited", "Thornfield Maintenance Limited"),
    ("Ravensworth Capital Limited", "Bramley Analytics Limited"),
]

SUBJECTS = [
    "Services Agreement",
    "Supply Agreement",
    "Consultancy Agreement",
    "Maintenance Agreement",
    "Distribution Agreement",
]

DEFINITIONS = [
    ("Agreement", "this agreement including its schedules and any annexes to it"),
    ("Business Day", "a day other than a Saturday, Sunday or public holiday in England"),
    ("Charges", "the sums payable by the Customer to the Supplier under this Agreement"),
    ("Commencement Date", "the date on which this Agreement is signed by both parties"),
    ("Deliverables", "the items the Supplier is to provide as set out in Schedule 1"),
    ("Services", "the services described in Schedule 1"),
]

OBLIGATIONS = [
    "The Supplier shall provide the Services with reasonable skill and care.",
    "The Supplier shall provide the Deliverables by the dates set out in Schedule 1.",
    (
        "The Customer shall give the Supplier such access to its premises as the "
        "Supplier reasonably requires in order to provide the Services."
    ),
    "The Customer shall pay the Charges within 30 days of receipt of a valid invoice.",
    "Each party shall keep the other party's confidential information confidential.",
    (
        "Neither party shall assign this Agreement without the other party's prior "
        "written consent, such consent not to be unreasonably withheld."
    ),
    (
        "The Supplier shall maintain insurance appropriate to the Services throughout "
        "the term of this Agreement."
    ),
    "Either party may terminate this Agreement on 30 days' written notice.",
]

SUB_OBLIGATIONS = [
    "keep proper records of the work carried out;",
    "notify the other party promptly of anything likely to cause delay;",
    "comply with all applicable laws and regulations;",
    "not do anything that brings the other party into disrepute.",
]


def make_contract(seed: int) -> Contract:
    """Build a structurally sound contract. Same seed, same contract."""
    rng = random.Random(seed)
    customer, supplier = rng.choice(PARTIES)
    subject = rng.choice(SUBJECTS)
    name = f"{subject.lower().replace(' ', '-')}-{seed:03d}"

    blocks: list[Block] = [
        Block(BlockKind.TITLE, f"{subject.upper()}"),
        Block(
            BlockKind.BODY,
            f'This Agreement is made between {customer} (the "Customer") and '
            f'{supplier} (the "Supplier").',
        ),
    ]

    clause = 0

    # 1. Definitions
    clause += 1
    blocks.append(Block(BlockKind.HEADING, "DEFINITIONS", level=1, number=str(clause)))
    for term, meaning in DEFINITIONS:
        blocks.append(
            Block(
                BlockKind.DEFINITION,
                f'"{term}" means {meaning}.',
                level=2,
                term=term,
            )
        )

    # 2-n. Substantive clauses, some with sub-clauses.
    headings = ["THE SERVICES", "CHARGES AND PAYMENT", "CONFIDENTIALITY", "TERM AND TERMINATION"]
    obligations = list(OBLIGATIONS)
    rng.shuffle(obligations)

    for heading in headings:
        clause += 1
        blocks.append(Block(BlockKind.HEADING, heading, level=1, number=str(clause)))
        for sub in range(1, rng.randint(2, 3) + 1):
            text = obligations.pop() if obligations else OBLIGATIONS[0]
            blocks.append(Block(BlockKind.BODY, text, level=2, number=f"{clause}.{sub}"))
            if sub == 1 and rng.random() < 0.5:
                blocks.append(
                    Block(
                        BlockKind.BODY,
                        "Each party shall:",
                        level=2,
                        number=f"{clause}.{sub + 1}",
                    )
                )
                sub += 1
                for letter, item in zip("abcd", SUB_OBLIGATIONS, strict=False):
                    blocks.append(Block(BlockKind.BODY, item, level=3, number=f"({letter})"))

    blocks.append(Block(BlockKind.SCHEDULE_TITLE, "SCHEDULE 1 - THE SERVICES"))
    blocks.append(
        Block(
            BlockKind.BODY,
            "The Supplier shall provide the Services described in this Schedule "
            "from the Commencement Date.",
        )
    )

    return Contract(name=name, blocks=blocks)
