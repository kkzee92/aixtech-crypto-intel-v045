# AIxTech crypto intel v0.45: paper-only trading information system

Research harness for automated cryptocurrency **information** and paper strategy evaluation. It does not place live orders, does not store exchange secrets, and is not financial advice.

Builds on [zeekiankok92/aixtech-crypto-intel](https://github.com/zeekiankok92/aixtech-crypto-intel) and successive enhancements under kkzee92.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![version](https://img.shields.io/badge/version-0.45.0-blue)
![mode](https://img.shields.io/badge/execution-paper%20only-orange)
![Licence](https://img.shields.io/badge/licence-MIT-green)

## What it does

- Classifies markets into eight asset classes and applies a different research rule to each, now with Bollinger Band squeeze/breakout proxies, volume-profile concentration, adaptive volatility clustering, and refined RSI divergence.
- Labels each series trend, range, or stress, and stands aside in stress.
- Scores a signal with multi-factor confirmation (EMA, RSI, volume, Ichimoku, ADX, Bollinger, vol-profile) then a risk gate that can shrink or refuse it.
- Applies a declared round-trip cost by asset class in the paper backtest (stub).
- Writes a hash-chained audit log with UTC timestamps, sealed Merkle-style multi-hash lineage, redacts secret-like strings including BIP39 seeds, private keys, Solana keys, and session tokens.
- Backtests on **synthetic** candles only. Network access is injectable and unused by default.

| Asset class | Research rule | Risk cap | Cost |
|---|---|---|---|
| Major (BTC, ETH) | Multi-factor EMA + ADX>25 + Ichimoku + Bollinger squeeze outside stress; range-only RSI reversion with divergence | 8% | 8 bps |
| Large-cap alt | Breakout with volume, ADX, Ichimoku, Bollinger, suppressed in stress | 4% | 14 bps |
| Stablecoin | 20 bp watch, 50 bp depeg alert. No order | 0% | n/a |
| DeFi | Trend only in a calm, non-stress regime with ADX, Ichimoku, vol-profile | 2% | 22 bps |
| Meme | Qualified burst with volume and ADX, chase filter, vol-profile concentration, 3-bar horizon | 0.5% | 45 bps |
| L2 | Relative strength versus a non-stress benchmark with ADX and Bollinger | 3% | 16 bps |
| RWA | Slow trend with ADX; halt on an 8% gap or stress | 2% | 12 bps |
| Perpetual | Negative-funding carry if drift contained and ADX ok; crowded funding is an alert | 2% | 10 bps |

Full notes: [docs/asset-class-strategies.md](docs/asset-class-strategies.md).
Security design: [docs/security-architecture.md](docs/security-architecture.md).
Latest: [docs/v045-enhanced-bollinger-volprofile-and-cyber.md](docs/v045-enhanced-bollinger-volprofile-and-cyber.md).

## Run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
PYTHONPATH=src python -c "from crypto_intel.strategies import signal_for; print('ready')"
```

The fixture is labelled `SYNTHETIC` and is not a market history.

## Controls

1. Paper-only execution. Any live mode raises `PermissionError`.
2. Trade and withdrawal credential names are refused. No role can place an order.
3. Class size caps, confidence floors, kill switch (stub), drawdown halt, stress overlay, multi-factor filters including Bollinger and vol-profile.
4. Hash-chained audit log with timestamps and sealed Merkle multi-hash, source attestation, feed checks, anomaly scores.
5. PDPA-style tripwire over fixtures and docs.
6. Expanded redaction for seeds, private keys, Solana, session tokens, hardware exports.

## Honesty

- No live exchange connector is included. Do not add trade keys to this tree.
- Strategy scores describe the synthetic fixture, not future returns.
- This is not legal, compliance, or investment advice.
