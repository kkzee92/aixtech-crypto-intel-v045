"""Core data models for paper research."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class AssetClass(str, Enum):
    MAJOR = "major"
    LARGE_CAP_ALT = "large_cap_alt"
    STABLECOIN = "stablecoin"
    DEFI = "defi"
    MEME = "meme"
    L2 = "l2"
    RWA = "rwa"
    PERPETUAL = "perpetual"


class Side(str, Enum):
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"
    ALERT = "alert"


class Regime(str, Enum):
    TREND = "trend"
    RANGE = "range"
    STRESS = "stress"


@dataclass
class Candle:
    symbol: str
    asset_class: AssetClass
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    funding_rate: float = 0.0


@dataclass
class Signal:
    symbol: str
    asset_class: AssetClass
    side: Side
    confidence: float
    reason: str
    stop_distance_pct: float
    size_fraction: float
    horizon_bars: int
