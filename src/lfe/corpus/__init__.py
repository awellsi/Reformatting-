"""Synthetic test corpus (M0).

A development tool, not part of the analysis pipeline: it manufactures the ugly
documents the analyser and normaliser are tested against, along with the clean
baselines they should be judged by.
"""

from .build import build
from .content import make_contract
from .model import Block, BlockKind, Contract

__all__ = ["Block", "BlockKind", "Contract", "build", "make_contract"]
