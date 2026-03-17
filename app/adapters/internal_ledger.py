from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from typing import Any

from app.adapters.base import RailAdapter, SettlementInstruction, SettlementResult

_SETTLE_SECONDS = 1


class InternalLedgerAdapter(RailAdapter):
    """SIMULATION ONLY — no real network calls."""

    def execute(self, instruction: SettlementInstruction) -> SettlementResult:
        reference_id = f"INT-{uuid4()}"
        return SettlementResult(
            rail="INTERNAL_LEDGER",
            reference_id=reference_id,
            status="SETTLED",
            settle_time_seconds=_SETTLE_SECONDS,
            settled_at=datetime.now(timezone.utc).isoformat(),
        )

    def capabilities(self) -> dict[str, Any]:
        return {
            "rail": "INTERNAL_LEDGER",
            "currency": ["USD", "CREDITS"],
            "max_amount": None,
        }
