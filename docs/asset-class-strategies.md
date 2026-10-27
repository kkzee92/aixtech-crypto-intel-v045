# Asset-class strategy notes v0.45

Research heuristics only. Not forecasts.

Regime from regime.py: trend / range / stress.

## Major
EMA trend + ADX>25 + Ichimoku above cloud + Bollinger mid + vol clustering <1.5. Range reversion with RSI washout + divergence + BB lower. Cap 8%.

## Large-cap alt
Volume breakout + ADX + Ichimoku + BB upper. Cap 4%.

## Stablecoin
Peg watch/depeg alert only. Size 0.

## DeFi
Calm trend + ADX + Ichimoku + vol-profile concentration. Cap 2%.

## Meme
Qualified burst + ADX + vol concentration. Cap 0.5%, 3-bar horizon.

## L2
Relative strength vs non-stress benchmark + ADX + BB. Cap 3%.

## RWA
Slow trend + ADX, gap halt. Cap 2%.

## Perpetual
Negative funding carry if drift contained + ADX ok. Cap 2%.

Still out of scope: live orders, trade keys, return claims.
