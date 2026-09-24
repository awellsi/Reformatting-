# Legal Format Engine

Turn messy legal `.docx` files into structurally correct documents that match a
house style, and **prove nothing else changed**.

Two surfaces:

1. **Health Check** — free, runs 100% in the browser, scores a `.docx` 0–100.
2. **Format Engine** — Python library + HTTP API + MCP server that normalises a
   `.docx` against a house style and returns a conformance report.

## Status

Skeleton only. No analysis or normalisation is implemented yet — `lfe check`
and `lfe fix` are registered and exit with "not implemented". See the milestones
in [CLAUDE.md](CLAUDE.md); M0 (test corpus) is next.

## Requirements

Python 3.12 or newer, managed with [uv](https://docs.astral.sh/uv/).

## Setup

```sh
uv python install 3.12
uv venv --python 3.12
uv pip install -e ".[dev]"
.venv/bin/pytest
```

## Usage

Once M1 lands:

```sh
lfe check contract.docx
```

Until then the only thing that runs end to end is the test suite.

## The guarantee

Body text is identical before and after. Every run re-extracts text from the
input and the output and fails loudly on any difference. Tracked changes,
comments, headers and footers, images and section breaks survive. No document
content is logged or stored.
