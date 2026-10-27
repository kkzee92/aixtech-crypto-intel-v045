# v0.45 Enhancements: Bollinger Squeeze, Volume Profile, Adaptive Clustering, and Cyber Security

## Strategy improvements per asset class

- **Major**: Added Bollinger Band mid/upper confirmation and volatility clustering filter (recent/longer vol ratio <1.5) to trend entries; RSI divergence for range reversion.
- **Large-cap alt**: Bollinger upper break confirmation on volume breakouts.
- **DeFi**: Volume-profile concentration (>0.15) as additional calm-regime filter.
- **Meme**: Volume concentration (>0.2) to qualify bursts, reducing noise.
- **L2**: Bollinger mid confirmation on relative strength.
- Shared: Adaptive vol clustering proxy, refined RSI divergence, volume-profile concentration proxy.

All remain paper-only research heuristics on synthetic data. No live execution.

## Security architecture enhancements

- Expanded redaction patterns for Solana-style keys, additional BIP39 word-list fragments, hardware wallet exports, and session tokens.
- Merkle-style multi-hash sealed lineage in audit log (hash of previous + current + timestamp).
- Anomaly detection proxy: statistical outlier on volume or price jumps feeds into risk gate (stub).
- Zero-trust isolation notes: separate research/audit/operator contexts; no shared secrets.
- Data residency stamp remains; feed integrity checks unchanged.

See security.py for redaction implementation (to be expanded in full push).

## Honesty

This is research infrastructure only. Scores do not predict returns. No trade keys, no live orders.
