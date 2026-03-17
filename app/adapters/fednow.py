from __future__ import annotations
import random
from datetime import datetime, timezone
from typing import Any

from app.adapters.base import RailAdapter, SettlementInstruction, SettlementResult

_SUCCESS_RATE = 0.995
_SETTLE_SECONDS = 3


class FedNowAdapter(RailAdapter):
    """SIMULATION ONLY — no real network calls."""

    def execute(self, instruction: SettlementInstruction) -> SettlementResult:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        digits = "".join([str(random.randint(0, 9)) for _ in range(5)])
        reference_id = f"FN{date_str}-{digits}"

        if random.random() < _SUCCESS_RATE:
            return SettlementResult(
                rail="FEDNOW",
                reference_id=reference_id,
                status="SETTLED",
                settle_time_seconds=_SETTLE_SECONDS,
                settled_at=datetime.now(timezone.utc).isoformat(),
            )
        return SettlementResult(
            rail="FEDNOW",
            reference_id=reference_id,
            status="FAILED",
            settle_time_seconds=_SETTLE_SECONDS,
            failure_reason="FEDNOW_SIM_RANDOM_FAILURE",
        )

    def capabilities(self) -> dict[str, Any]:
        return {
            "rail": "FEDNOW",
            "currency": ["USD"],
            "max_amount": 500000,
        }
