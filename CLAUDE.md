# Project: Legal Format Engine

## Mission
Turn messy legal .docx files into structurally correct documents that match a
house style, and PROVE nothing else changed. Two surfaces:
1. Health Check — free, runs 100% in the browser, scores a .docx 0–100.
2. Format Engine — Python library + HTTP API + MCP server that normalises a
   .docx against a house style and returns a conformance report.

## Non-negotiables
- Body text must be identical before/after. Every run re-extracts text from
  input and output and fails loudly on any diff (whitespace-normalised).
- Never drop tracked changes, comments, headers/footers, images, section breaks.
- Deterministic writes. An LLM may ONLY classify ambiguous paragraphs
  (heading level / list item / body / definition / schedule title) and must
  return a confidence. Below threshold -> flag in report, do not guess.
- No document content is logged or stored. API processes in memory, deletes on
  response. Health Check never uploads.
- Output must open cleanly in Word (Win + Mac) and LibreOffice.

## Stack
- Core: Python 3.12, lxml operating directly on OOXML (python-docx only for
  convenience reads). Package: `lfe` (pip-installable).
- Health Check: the same analysis rules compiled to run in-browser via
  Pyodide, OR a TypeScript port of the analyser only (pick after spike, M1).
- API: FastAPI, stateless, Docker. Stripe for billing, API keys per customer.
- MCP server exposing `analyse_docx` and `normalise_docx`.
- Rendering check: LibreOffice headless -> PDF -> page images for visual diff.

## Architecture
ingest -> parse to internal model (paragraphs, runs, numbering instances,
styles, fields) -> analyse (rules produce Findings) -> classify (rules first,
LLM fallback) -> plan (list of edit ops) -> apply ops to the ORIGINAL XML
(patch, never regenerate) -> verify (text-identity, schema-valid, re-analyse
score) -> report JSON.

## House style spec (v1)
Either a reference .docx (extract its styles + numbering) or JSON:
heading levels 1–4 -> style + numbering format (1 / 1.1 / (a) / (i)),
body style, definitions style, font, size, spacing, margins, page-number
format, signature block style.

## Analysis rules (each = id, severity, locator, auto-fixable?)
NUM-001 typed numbers masquerading as list numbering
NUM-002 parallel numbering instances in one outline (restarts/skips)
NUM-003 list level inconsistent with visual indent
STY-001 non-template styles in use ("Normal (2)", "Heading 1 Char")
STY-002 direct formatting overriding style (font, size, spacing)
XRF-001 cross-reference field pointing to missing/moved bookmark
XRF-002 typed "clause 4.3" references not linked to fields
TOC-001 TOC stale vs headings
DEF-001 defined term used but never defined / defined but never used
CLN-001 leftover highlights, [placeholders], comments marked resolved

## Milestones
M0 Test corpus: 40 synthetic ugly contracts (generate with python: pasted
   clauses, three-firm style soup, typed numbering, broken xrefs) + golden
   expected outputs. Ask the owner for 10 real anonymised docs. No client docs.
M1 Analyser + scoring + CLI `lfe check file.docx`. Spike Pyodide vs TS.
M2 Health Check web page (single static page, drag-drop, score card,
   shareable PNG of the score, email capture for "fix it").
M3 Normaliser: styles + numbering rebuild + direct-formatting strip.
   Text-identity verifier. CLI `lfe fix in.docx --style house.docx`.
M4 Cross-refs + TOC rebuild + defined-terms check.
M5 LLM classifier for ambiguous paragraphs (Claude API, confidence,
   batched, cached by paragraph hash). Report JSON schema v1.
M6 FastAPI + API keys + Stripe metered billing + Dockerfile. MCP server.
M7 Visual regression: render before/after via LibreOffice, image diff report.

## Definition of done (every milestone)
- pytest green on full corpus; text-identity passes on 100% of corpus.
- Score after fix >= 90 on 90% of corpus.
- Opens without repair prompt in LibreOffice; owner spot-checks 5 in Word.
- README updated with one runnable example.

## Working style
- Small commits, one rule or op per PR-sized change, tests first.
- When unsure how Word stores something, create a minimal .docx in the
  corpus that demonstrates it and read the XML; do not guess.
- Ask the owner before adding any dependency with a non-permissive licence.
