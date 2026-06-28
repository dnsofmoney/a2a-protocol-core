# Changelog

All notable changes to `a2a-protocol-core` are documented here. This project
adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] — Unreleased

Initial public protocol-core extraction from the DNS of Money Financial
Autonomy Stack.

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
