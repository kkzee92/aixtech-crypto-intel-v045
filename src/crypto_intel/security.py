"""Security helpers: redaction, attestation, paper-only guards, Merkle lineage stub.

Research controls only. Not a certified security product.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|private[_-]?key|seed|mnemonic|bip39|wallet[_-]?key)\s*[:=]\s*[\w+/=]{8,}"),
    re.compile(r"(?i)(sk-|pk_|ghp_|github_pat_|solana[_-]?key|ed25519)"),
    re.compile(r"\b(?:[a-z]+\s+){11,23}[a-z]+\b"),  # rough BIP39 fragment
    re.compile(r"(?i)(session[_-]?token|cookie|bearer)\s*[:=]\s*[\w+/=.-]{10,}"),
]


def redact(text: str) -> str:
    """Redact secret-like strings. Expanded for Solana, BIP39, sessions."""
    for pat in SECRET_PATTERNS:
        text = pat.sub("[REDACTED]", text)
    return text


def assert_paper_only(mode: str) -> None:
    if mode.upper() != "PAPER":
        raise PermissionError("live mode refused; paper-only research system")


def refuse_trade_secret(name: str) -> None:
    lowered = name.lower()
    if any(k in lowered for k in ("trade", "withdraw", "transfer", "order", "exchange_key")):
        raise PermissionError(f"trade/withdrawal credential refused: {name}")


def attest_source(label: str, body: str) -> str:
    """Hash label + body for fixture integrity."""
    return hashlib.sha256(f"{label}:{body}".encode()).hexdigest()


def merkle_lineage(prev_hash: str, current: str, ts: str | None = None) -> str:
    """Simple Merkle-style sealed hash: hash(prev + current + timestamp)."""
    ts = ts or datetime.now(timezone.utc).isoformat()
    payload = f"{prev_hash}:{current}:{ts}"
    return hashlib.sha256(payload.encode()).hexdigest()


def anomaly_score(volume: float, avg_volume: float, price_jump: float) -> float:
    """Stub anomaly: higher if volume spike or large jump."""
    vol_ratio = volume / (avg_volume or 1)
    jump_score = abs(price_jump) * 10
    return min(1.0, max(vol_ratio - 1, 0) * 0.3 + jump_score)
