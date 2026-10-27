# Security architecture v0.45

Research design only. Not certified, not legal advice.

## Trust boundaries

Paper-only. No order router. `assert_paper_only` refuses non-PAPER. `refuse_trade_secret` rejects trade/withdraw names.

## Roles

Researcher / Auditor / Operator: scan, read audit, kill switch. None can place orders.

## Data classes and handling

- Public market data: synthetic only.
- Secrets: redacted via expanded patterns (Solana keys, BIP39 fragments, session tokens, hardware exports).
- Personal data: PDPA tripwire.

## Feed integrity and lineage

`attest_source` + `merkle_lineage` for sealed multi-hash chain with timestamps.
Anomaly score stub on volume/price jumps feeds risk gate.

## Threats and controls

| Threat | Control |
|---|---|
| Secret committed | gitleaks + expanded redaction |
| Trade key | refuse_trade_secret |
| Fixture injection | SYNTHETIC label + attestation |
| Audit tamper | Merkle sealed hash chain |
| Live mistake | paper-only guard + no live client |
| Anomaly | volume/price outlier score |

## Incident handling

Kill switch, freeze audit, rotate external secrets, human review.
