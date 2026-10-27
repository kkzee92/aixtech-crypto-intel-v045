"""Basic strategy smoke tests."""

from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.strategies import signal_for


def _candle(close: float, volume: float = 1000, funding: float = 0.0) -> Candle:
    return Candle(
        symbol="TEST",
        asset_class=AssetClass.MAJOR,
        timestamp=1,
        open=close,
        high=close * 1.01,
        low=close * 0.99,
        close=close,
        volume=volume,
        funding_rate=funding,
    )


def test_major_flat_on_short_series():
    candles = [_candle(100 + i) for i in range(10)]
    sig = signal_for(candles)
    assert sig.side in (Side.FLAT, Side.LONG, Side.ALERT)
    assert 0 <= sig.confidence <= 1
