from __future__ import annotations
import random
import string
from datetime import datetime, timezone
from typing import Any

from app.adapters.base import RailAdapter, SettlementInstruction, SettlementResult

_SUCCESS_RATE = 0.999
_SETTLE_SECONDS = 4


class XRPLAdapter(RailAdapter):
    """SIMULATION ONLY — no real network calls."""

    def execute(self, instruction: SettlementInstruction) -> SettlementResult:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        hex_suffix = "".join(random.choices(string.hexdigits.lower()[:16], k=8))
        reference_id = f"XRPL-{date_str}-{hex_suffix}"

        if random.random() < _SUCCESS_RATE:
            return SettlementResult(
                rail="XRPL",
                reference_id=reference_id,
                status="SETTLED",
                settle_time_seconds=_SETTLE_SECONDS,
                settled_at=datetime.now(timezone.utc).isoformat(),
            )
        return SettlementResult(
            rail="XRPL",
            reference_id=reference_id,
            status="FAILED",
            settle_time_seconds=_SETTLE_SECONDS,
            failure_reason="XRPL_SIM_RANDOM_FAILURE",
        )

    def capabilities(self) -> dict[str, Any]:
        return {
            "rail": "XRPL",
            "currency": ["XRP", "USD"],
            "max_amount": None,
        }
