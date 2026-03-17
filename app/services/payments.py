from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from app.adapters.base import RailAdapter, SettlementInstruction
from app.core.semantic_normalizer import normalize_semantics
from app.services.resolver import FASResolver


@dataclass
class PaymentRequest:
    payer_agent_id: str
    payee_alias: str
    amount: float
    currency: str
    request_id: str
    policy: Optional[dict] = None


@dataclass
class PaymentResult:
    payment_id: str
    request_id: str
    payee_alias: str
    selected_rail: str
    amount: float
    currency: str
    status: str
    settlement_ref: Optional[str]
    settled_at: Optional[str]
    receipt_ref: str


class PaymentOrchestrator:
    def __init__(
        self,
        resolver: FASResolver,
        adapters: dict[str, RailAdapter],
    ) -> None:
        self._resolver = resolver
        self._adapters = adapters

    def execute(self, request: PaymentRequest) -> PaymentResult:
        # Step 1: semantic normalization
        normalize_semantics(
            f"settle payment to {request.payee_alias}",
            domain="FINTECH",
        )

        # Step 2: resolve alias
        record = self._resolver.resolve(request.payee_alias)
        if record is None:
            return PaymentResult(
                payment_id=str(uuid4()),
                request_id=request.request_id,
                payee_alias=request.payee_alias,
                selected_rail="NONE",
                amount=request.amount,
                currency=request.currency,
                status="FAILED",
                settlement_ref=None,
                settled_at=None,
                receipt_ref=f"RCPT-{uuid4()}",
            )

        # Step 3: select rail
        endpoint = self._resolver.select_rail(record, request.policy)

        # Step 4: build instruction
        instruction = SettlementInstruction(
            rail=endpoint.rail,
            payer_id=request.payer_agent_id,
            payee_address=endpoint.address,
            amount=request.amount,
            currency=request.currency,
            reference_id=request.request_id,
            iso_hint=record.iso_hint,
        )

        # Step 5: execute
        adapter = self._adapters.get(endpoint.rail)
        if adapter is None:
            return PaymentResult(
                payment_id=str(uuid4()),
                request_id=request.request_id,
                payee_alias=request.payee_alias,
                selected_rail=endpoint.rail,
                amount=request.amount,
                currency=request.currency,
                status="FAILED",
                settlement_ref=None,
                settled_at=None,
                receipt_ref=f"RCPT-{uuid4()}",
            )

        result = adapter.execute(instruction)

        # Step 6: return PaymentResult
        return PaymentResult(
            payment_id=str(uuid4()),
            request_id=request.request_id,
            payee_alias=request.payee_alias,
            selected_rail=result.rail,
            amount=request.amount,
            currency=request.currency,
            status=result.status,
            settlement_ref=result.reference_id,
            settled_at=result.settled_at,
            receipt_ref=f"RCPT-{uuid4()}",
        )
