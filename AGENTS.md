# AGENTS.md — A2A Protocol Core

## Required pipeline
raw_input
  → normalize_semantics()        [A2A-009 — app/core/semantic_normalizer.py]
  → canonical semantic form + semantic_hash
  → canonicalize_message()       [A2A-008 — app/core/a2a_core.py]
  → canonical_hash
  → route / execute / settle

## Rules
- Preserve A2A-001 through A2A-060 naming
- Never merge into financial-autonomy-stack
- Typed Python throughout
- Simulation only — no real banking integrations
