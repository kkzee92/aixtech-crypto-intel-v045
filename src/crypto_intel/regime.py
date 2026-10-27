"""Regime classification for research overlay."""

from __future__ import annotations

from statistics import fmean

from crypto_intel.models import Candle, Regime


def atr_pct(candles: list[Candle], period: int = 14) -> float:
    ranges = [(c.high - c.low) / c.close for c in candles[-period:] if c.close]
    return fmean(ranges) if ranges else 0.0


def classify(candles: list[Candle]) -> Regime:
    if len(candles) < 8:
        return Regime.RANGE
    closes = [c.close for c in candles]
    move = abs(closes[-1] / closes[-8] - 1.0)
    bar_range = atr_pct(candles)
    if bar_range >= 0.035:
        return Regime.STRESS
    if move >= 0.025 and bar_range < 0.035:
        return Regime.TREND
    return Regime.RANGE
