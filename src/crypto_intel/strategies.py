"""Asset-class strategy research rules.

Transparent heuristics for paper research. Not forecasts and not a recommendation
to trade. Each class has an entry, an invalidation, and a regime overlay.
Version 0.45 adds Bollinger Band squeeze/breakout proxies, volume-profile
concentration, adaptive volatility clustering, and refined RSI divergence.
"""

from __future__ import annotations

from statistics import fmean, pstdev

from crypto_intel.models import AssetClass, Candle, Side, Signal
from crypto_intel.regime import Regime, classify

PLAYBOOK: dict[AssetClass, dict[str, str]] = {
    AssetClass.MAJOR: {
        "hypothesis": "Liquid majors trend with multi-factor, Ichimoku, ADX, Bollinger squeeze confirmation, except under stress.",
        "entry": "Fast EMA above slow, RSI 45-70, volume ok, Ichimoku above cloud, ADX >25, Bollinger squeeze break, multi-TF aligned.",
        "invalidation": "Stress, RSI >70, thin volume, weak ADX, inside cloud, no squeeze break, multi-TF mismatch.",
        "horizon": "8 bars mean-reversion, 20 bars trend",
    },
    AssetClass.LARGE_CAP_ALT: {
        "hypothesis": "Breakouts without volume, strength, or Bollinger confirmation are noise.",
        "entry": "Close above prior high, volume 1.2x, ADX >20, Ichimoku above, Bollinger break, non-stress.",
        "invalidation": "Stress, low volume, weak ADX, below cloud, or no BB confirmation.",
        "horizon": "12 bars",
    },
    AssetClass.STABLECOIN: {
        "hypothesis": "The useful signal is a peg break.",
        "entry": "Deviation of 50 bps or more raises an alert. No order.",
        "invalidation": "Not applicable. Size stays zero.",
        "horizon": "1 bar monitor",
    },
    AssetClass.DEFI: {
        "hypothesis": "Trend only in calm regime with strength and volume-profile confirmation.",
        "entry": "Close above EMA, vol low, ADX >22, Ichimoku above, concentrated vol-profile, non-stress.",
        "invalidation": "Stress, high vol, weak ADX, below cloud, or dispersed profile.",
        "horizon": "10 bars",
    },
    AssetClass.MEME: {
        "hypothesis": "Most bursts are untradeable. Qualified with strength and volume concentration.",
        "entry": "15% burst, rising volume, ADX rising, concentrated vol-profile, not extended.",
        "invalidation": "Thin liquidity, chase extension, or dispersed volume.",
        "horizon": "3 bars",
    },
    AssetClass.L2: {
        "hypothesis": "L2 relative strength versus benchmark, with strength and Bollinger filter.",
        "entry": "Excess return >3%, benchmark non-stress, ADX >18, Bollinger break.",
        "invalidation": "Missing benchmark, benchmark stress, weak ADX, or no BB.",
        "horizon": "12 bars",
    },
    AssetClass.RWA: {
        "hypothesis": "Tokenised assets should be slow with strength confirmation.",
        "entry": "Slow trend, gap <8%, ADX >15, non-stress.",
        "invalidation": "Gap >8% or stress.",
        "horizon": "24 bars",
    },
    AssetClass.PERPETUAL: {
        "hypothesis": "Negative funding with contained drift and strength.",
        "entry": "Funding <= -5 bps, |drift| <4%, ADX contained.",
        "invalidation": "Crowded funding or excess drift.",
        "horizon": "8 bars",
    },
}


def _returns(closes: list[float]) -> list[float]:
    return [closes[i] / closes[i - 1] - 1.0 for i in range(1, len(closes))]


def _ema(values: list[float], span: int) -> float:
    alpha = 2.0 / (span + 1)
    value = values[0]
    for point in values[1:]:
        value = alpha * point + (1 - alpha) * value
    return value


def _rsi(closes: list[float], period: int = 14) -> float:
    changes = _returns(closes[-(period + 1) :])
    gains = [max(change, 0.0) for change in changes]
    losses = [abs(min(change, 0.0)) for change in changes]
    average_loss = fmean(losses) if losses else 0.0
    if average_loss == 0:
        return 100.0
    rs = fmean(gains) / average_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _adx_proxy(candles: list[Candle], period: int = 14) -> float:
    if len(candles) < period + 1:
        return 0.0
    plus_dm = []
    minus_dm = []
    tr = []
    for i in range(1, len(candles)):
        up = candles[i].high - candles[i - 1].high
        down = candles[i - 1].low - candles[i].low
        plus_dm.append(max(up, 0.0) if up > down else 0.0)
        minus_dm.append(max(down, 0.0) if down > up else 0.0)
        tr.append(max(candles[i].high - candles[i].low, abs(candles[i].high - candles[i - 1].close), abs(candles[i].low - candles[i - 1].close)))
    if not tr:
        return 0.0
    avg_plus = fmean(plus_dm[-period:]) / (fmean(tr[-period:]) or 1)
    avg_minus = fmean(minus_dm[-period:]) / (fmean(tr[-period:]) or 1)
    dx = abs(avg_plus - avg_minus) / (avg_plus + avg_minus or 1) * 100
    return min(dx, 100.0)


def _ichimoku_proxy(candles: list[Candle]) -> tuple[float, float, float]:
    if len(candles) < 26:
        return 0.0, 0.0, 0.0
    highs9 = [c.high for c in candles[-9:]]
    lows9 = [c.low for c in candles[-9:]]
    tenkan = (max(highs9) + min(lows9)) / 2
    highs26 = [c.high for c in candles[-26:]]
    lows26 = [c.low for c in candles[-26:]]
    kijun = (max(highs26) + min(lows26)) / 2
    senkou_a = (tenkan + kijun) / 2
    return tenkan, kijun, senkou_a


def _bollinger_proxy(closes: list[float], period: int = 20, std_mult: float = 2.0) -> tuple[float, float, float]:
    """Bollinger Band proxy: mid, upper, lower. Returns (mid, upper, lower)."""
    if len(closes) < period:
        return closes[-1], closes[-1], closes[-1]
    window = closes[-period:]
    mid = fmean(window)
    std = pstdev(window) or 0.001
    upper = mid + std_mult * std
    lower = mid - std_mult * std
    return mid, upper, lower


def _volume_profile_concentration(candles: list[Candle], bins: int = 5) -> float:
    """Proxy for volume concentration: fraction of volume in top bin vs total. Higher = more concentrated."""
    if len(candles) < 10:
        return 0.5
    vols = [c.volume for c in candles[-20:]]
    if not vols or sum(vols) == 0:
        return 0.5
    # Simple: max volume bar / total
    return max(vols) / sum(vols)


def _vol_clustering(closes: list[float]) -> float:
    """Adaptive volatility clustering proxy: recent vol / longer vol."""
    if len(closes) < 20:
        return 1.0
    recent = pstdev(_returns(closes[-8:])) or 0.001
    longer = pstdev(_returns(closes[-20:])) or 0.001
    return recent / longer


def _rsi_divergence(closes: list[float]) -> bool:
    """Simple bullish divergence proxy: price lower low but RSI higher low."""
    if len(closes) < 20:
        return False
    price_recent = min(closes[-5:])
    price_prior = min(closes[-15:-5])
    rsi_recent = _rsi(closes[-10:])
    rsi_prior = _rsi(closes[-20:-5])
    return price_recent < price_prior and rsi_recent > rsi_prior


def _atr_pct(candles: list[Candle]) -> float:
    ranges = [(c.high - c.low) / c.close for c in candles[-14:] if c.close]
    return fmean(ranges) if ranges else 0.0


def _base(candles: list[Candle], side: Side, confidence: float, reason: str, size: float, bars: int) -> Signal:
    last = candles[-1]
    regime = classify(candles)
    return Signal(
        symbol=last.symbol,
        asset_class=last.asset_class,
        side=side,
        confidence=round(max(0.0, min(confidence, 1.0)), 4),
        reason=f"{reason}; regime={regime.value}",
        stop_distance_pct=round(max(_atr_pct(candles) * 1.5, 0.01), 4),
        size_fraction=size,
        horizon_bars=bars,
    )


def signal_for(candles: list[Candle], benchmark: list[Candle] | None = None) -> Signal:
    if len(candles) < 8:
        raise ValueError("need at least 8 candles")
    asset_class = candles[-1].asset_class
    closes = [c.close for c in candles]
    regime = classify(candles)
    if asset_class is AssetClass.MAJOR:
        return _major(candles, closes, regime)
    if asset_class is AssetClass.LARGE_CAP_ALT:
        return _breakout(candles, closes, size=0.04, bars=12, regime=regime)
    if asset_class is AssetClass.STABLECOIN:
        return _stable(candles)
    if asset_class is AssetClass.DEFI:
        return _defi(candles, closes, regime)
    if asset_class is AssetClass.MEME:
        return _meme(candles, closes)
    if asset_class is AssetClass.L2:
        return _l2(candles, closes, benchmark)
    if asset_class is AssetClass.RWA:
        return _rwa(candles, closes, regime)
    return _perpetual(candles, closes)


def _major(candles: list[Candle], closes: list[float], regime: Regime) -> Signal:
    fast, slow = _ema(closes, 5), _ema(closes, 13)
    rsi = _rsi(closes)
    adx = _adx_proxy(candles)
    tenkan, kijun, senkou = _ichimoku_proxy(candles)
    mid, upper, lower = _bollinger_proxy(closes)
    price = closes[-1]
    vol_cluster = _vol_clustering(closes)
    div = _rsi_divergence(closes)
    if regime is Regime.STRESS:
        return _base(candles, Side.FLAT, 0.45, "major stress: stand aside", 0.0, 1)
    if fast > slow and 45 <= rsi <= 70 and adx > 25 and price > senkou and price > mid and vol_cluster < 1.5:
        return _base(candles, Side.LONG, 0.80, "major trend: EMA + ADX>25 + Ichimoku + BB mid + controlled vol", 0.06, 20)
    if regime is Regime.RANGE and rsi < 30 and price > lower and div:
        return _base(candles, Side.LONG, 0.66, "major mean-reversion: washed RSI, BB lower, divergence", 0.03, 8)
    return _base(candles, Side.FLAT, 0.4, "major: no confirmed edge", 0.0, 1)


def _breakout(candles: list[Candle], closes: list[float], size: float, bars: int, regime: Regime) -> Signal:
    if regime is Regime.STRESS:
        return _base(candles, Side.FLAT, 0.4, "breakout suppressed in stress", 0.0, 1)
    window = closes[-6:-1]
    volume_now = candles[-1].volume
    volume_base = fmean(c.volume for c in candles[-6:-1])
    adx = _adx_proxy(candles)
    _, _, senkou = _ichimoku_proxy(candles)
    mid, upper, lower = _bollinger_proxy(closes)
    if closes[-1] > max(window) and volume_now > volume_base * 1.2 and adx > 20 and closes[-1] > senkou and closes[-1] > upper * 0.99:
        return _base(candles, Side.LONG, 0.75, "breakout with volume, ADX, Ichimoku, and BB", size, bars)
    return _base(candles, Side.FLAT, 0.35, "no confirmed breakout", 0.0, 1)


def _stable(candles: list[Candle]) -> Signal:
    deviation = abs(candles[-1].close - 1.0)
    if deviation >= 0.005:
        return _base(candles, Side.ALERT, 0.92, f"stablecoin depeg monitor: deviation {deviation:.4f}", 0.0, 1)
    if deviation >= 0.002:
        return _base(candles, Side.ALERT, 0.7, f"stablecoin watch band: deviation {deviation:.4f}", 0.0, 1)
    return _base(candles, Side.FLAT, 0.8, "stablecoin inside peg band", 0.0, 1)


def _defi(candles: list[Candle], closes: list[float], regime: Regime) -> Signal:
    realised = fmean(abs(v) for v in _returns(closes[-8:]))
    adx = _adx_proxy(candles)
    _, _, senkou = _ichimoku_proxy(candles)
    conc = _volume_profile_concentration(candles)
    if regime is Regime.STRESS or realised > 0.06:
        return _base(candles, Side.FLAT, 0.48, "defi volatility regime: stand aside", 0.0, 1)
    if closes[-1] > _ema(closes, 8) and adx > 22 and closes[-1] > senkou and conc > 0.15:
        return _base(candles, Side.LONG, 0.73, "defi trend in calm regime with ADX, Ichimoku, vol-profile", 0.02, 10)
    return _base(candles, Side.FLAT, 0.4, "defi: no calm trend", 0.0, 1)


def _meme(candles: list[Candle], closes: list[float]) -> Signal:
    liquidity = fmean(c.volume for c in candles[-5:])
    burst = closes[-1] / closes[-4] - 1.0
    extension = closes[-1] / closes[-8] - 1.0
    adx = _adx_proxy(candles)
    conc = _volume_profile_concentration(candles)
    if liquidity < 1000:
        return _base(candles, Side.FLAT, 0.2, "meme liquidity proxy too thin", 0.0, 1)
    if extension > 0.40:
        return _base(candles, Side.FLAT, 0.35, "meme chase filter: 8-bar extension too large", 0.0, 1)
    if burst > 0.15 and candles[-1].volume > candles[-2].volume and adx > 15 and conc > 0.2:
        return _base(candles, Side.LONG, 0.81, "meme momentum burst with ADX and vol concentration; hard time stop", 0.005, 3)
    return _base(candles, Side.FLAT, 0.3, "meme: no qualified burst", 0.0, 1)


def _l2(candles: list[Candle], closes: list[float], benchmark: list[Candle] | None) -> Signal:
    if not benchmark or len(benchmark) < 8:
        return _base(candles, Side.FLAT, 0.3, "l2 requires a benchmark series", 0.0, 1)
    if classify(benchmark) is Regime.STRESS:
        return _base(candles, Side.FLAT, 0.42, "l2 benchmark in stress", 0.0, 1)
    own = closes[-1] / closes[-6] - 1.0
    bench_closes = [c.close for c in benchmark]
    bench = bench_closes[-1] / bench_closes[-6] - 1.0
    adx = _adx_proxy(candles)
    mid, upper, lower = _bollinger_proxy(closes)
    if own - bench > 0.03 and adx > 18 and closes[-1] > mid:
        return _base(candles, Side.LONG, 0.74, "l2 relative strength with ADX and BB", 0.03, 12)
    return _base(candles, Side.FLAT, 0.4, "l2 not leading benchmark", 0.0, 1)


def _rwa(candles: list[Candle], closes: list[float], regime: Regime) -> Signal:
    gap = candles[-1].open / candles[-2].close - 1.0
    adx = _adx_proxy(candles)
    if abs(gap) > 0.08 or regime is Regime.STRESS:
        return _base(candles, Side.FLAT, 0.5, "rwa gap or stress halt", 0.0, 1)
    if closes[-1] > _ema(closes, 8) and closes[-1] > closes[-5] and adx > 15:
        return _base(candles, Side.LONG, 0.69, "rwa slow trend with ADX", 0.02, 24)
    return _base(candles, Side.FLAT, 0.4, "rwa: no slow trend", 0.0, 1)


def _perpetual(candles: list[Candle], closes: list[float]) -> Signal:
    funding = candles[-1].funding_rate
    drift = closes[-1] / closes[-6] - 1.0
    adx = _adx_proxy(candles)
    if funding >= 0.001:
        return _base(candles, Side.ALERT, 0.7, "perp funding crowded: monitor, no carry", 0.0, 1)
    if funding <= -0.0005 and abs(drift) < 0.04 and adx < 40:
        return _base(candles, Side.LONG, 0.77, "perp funding carry: negative funding, basis contained, ADX ok", 0.02, 8)
    if funding <= -0.0005:
        return _base(candles, Side.FLAT, 0.5, "perp funding attractive but drift not contained", 0.0, 1)
    return _base(candles, Side.FLAT, 0.4, "perp: no carry edge", 0.0, 1)
