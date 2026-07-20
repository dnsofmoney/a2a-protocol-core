# Changelog

All notable changes to `a2a-protocol-core` are documented here. This project
adheres to [Semantic Versioning](https://semver.org/).

## [0.2.1] — 2026-07-20

Conformance fix for the XRPL exact scheme's field placement. Required before
the server drops its deprecated top-level mirrors (scheduled after 2026-10-01)
— a 0.2.0 client will stop attaching `InvoiceID` at that point and be rejected
by the server's mandatory invoice binding.

### Fixed
- `pay_alias_xrp` now reads `invoiceId` and `sourceTag` from the x402
  requirement's `extra` block, where the XRPL exact scheme
  (`scheme_exact_xrpl.md`) places them, falling back to the deprecated
  top-level mirrors for not-yet-updated servers. Previously only the top-level
  copies were read, so a spec-conformant server that stopped mirroring them
  would silently produce payments without `InvoiceID` — which the invoice
  binding (the anti-replay mechanism) mandatorily rejects.

## [0.2.0] — 2026-07-11

Adds the one-call x402 pay-path so an agent can pay a `pay:` alias from its own
wallet — the "make it actually easy" client, still fully non-custodial.

### Added
- `pay_alias_xrp(...)` — resolve the x402 requirement for a `pay:` alias, sign +
  submit the XRP payment **locally with the caller's own seed** (the seed never
  leaves the process), then verify + fetch the signed resolve/verify/OFAC-screen
  attestation. One call, end to end.
- `attest_settled_payment(...)` — bring-your-own already-settled tx hash (e.g. an
  agent paying through its own wallet stack / a Coinbase Agentic Wallet) and get
  the read-only verify + attestation. No `[xrpl]` extra needed.
- Pure, network-free helpers: `fetch_requirement`, `decode_payment_required`,
  `build_x_payment_header`, `invoice_id_hash`, `summarize_attestation`, plus
  `AttestationSummary` / `X402PaymentResult` / `X402PayError`.
- New optional extra `[xrpl]` (pulls `xrpl-py`) — only needed for the local
  signing in `pay_alias_xrp`; the base install stays `pydantic` + `requests`.

## [0.1.0] — 2026-06-28

Initial public protocol-core extraction from the DNS of Money Financial
Autonomy Stack. Published to PyPI.

### Added
- `pay:` URI addressing (FAS-1 grammar): `is_valid_pay_uri`, `assert_valid_pay_uri`,
  `PAY_URI_PATTERN`.
- A2A-009 semantic normalizer: `normalize_action`, `normalize_message`,
  `compute_semantic_hash`, `SYNONYM_MAP`, `CANONICAL_ACTIONS`.
- A2A-008 canonical hashing: `compute_canonical_hash` — metadata-stable,
  vocabulary-stable payment-intent hashing.
- A2A-041 wire schemas: `A2APaymentHookRequest`, `A2APaymentHookResponse`,
  `ResolutionDetail`, `SettlementDetail`, `A2ACapabilities`.
- `A2APaymentHookClient` — synchronous payment-hook + capabilities client with
  client-side validation.
- Test suite covering addressing, normalization, canonical hashing, and schema
  validation.
- Apache-2.0 license, `py.typed` marker, runnable example.
