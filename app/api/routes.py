from __future__ import annotations
from dataclasses import asdict
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.core.semantic_normalizer import normalize_semantics
from app.services.messages import process_inbound
from app.services.payments import PaymentRequest
from app.services.receipts import Receipt
from app.services.registry import AgentRecord
from app.services.reputation import ReputationEvent

router = APIRouter()


# ── health ────────────────────────────────────────────────────────────────────

@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "1.0.0", "spec_family": "A2A-001-060"}


# ── agents ────────────────────────────────────────────────────────────────────

class AgentRegisterBody(BaseModel):
    agent_id: str
    org_id: str
    domain: str
    payment_alias: Optional[str] = None
    endpoint: Optional[str] = None
    trust_tier: str
    protocol_versions: list[str] = []
    message_types: list[str] = []
    input_schemas: list[str] = []
    output_schemas: list[str] = []
    tools: list[str] = []
    max_latency_ms: int = 1000
    created_at: str


@router.post("/agents/register")
def register_agent(body: AgentRegisterBody, request: Request) -> dict[str, Any]:
    record = AgentRecord(**body.model_dump())
    registered = request.app.state.registry.register(record)
    return asdict(registered)


@router.get("/agents/{agent_id}")
def get_agent(agent_id: str, request: Request) -> dict[str, Any]:
    record = request.app.state.registry.get(agent_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return asdict(record)


@router.get("/agents")
def list_agents(request: Request, domain: Optional[str] = None) -> list[dict[str, Any]]:
    if domain:
        records = request.app.state.registry.list_by_domain(domain)
    else:
        records = request.app.state.registry.all()
    return [asdict(r) for r in records]


# ── resolve ───────────────────────────────────────────────────────────────────

class ResolveBody(BaseModel):
    alias: str


@router.post("/resolve")
def resolve_alias(body: ResolveBody, request: Request) -> dict[str, Any]:
    # Normalize semantics first
    normalize_semantics(
        f"resolve {body.alias}",
        domain="FINTECH",
        require_min_confidence=False,
    )
    record = request.app.state.resolver.resolve(body.alias)
    if record is None:
        raise HTTPException(status_code=404, detail="Alias not found")
    from dataclasses import asdict as _asdict
    d = _asdict(record)
    return d


# ── messages ──────────────────────────────────────────────────────────────────

@router.post("/messages")
def inbound_message(message: dict[str, Any]) -> dict[str, Any]:
    try:
        return process_inbound(message)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


# ── payments ──────────────────────────────────────────────────────────────────

class PaymentBody(BaseModel):
    payer_agent_id: str
    payee_alias: str
    amount: float
    currency: str
    request_id: str
    policy: Optional[dict] = None


@router.post("/payments")
def create_payment(body: PaymentBody, request: Request) -> dict[str, Any]:
    req = PaymentRequest(**body.model_dump())
    result = request.app.state.orchestrator.execute(req)
    d = asdict(result)
    request.app.state.payment_results[result.payment_id] = d
    return d


@router.get("/payments/{payment_id}")
def get_payment(payment_id: str, request: Request) -> dict[str, Any]:
    result = request.app.state.payment_results.get(payment_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return result


# ── receipts ──────────────────────────────────────────────────────────────────

class ReceiptBody(BaseModel):
    request_id: str
    receipt_status: str
    receiver_agent_id: str
    timestamp: str
    payload_hash: str
    execution_ref: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@router.post("/receipts")
def create_receipt(body: ReceiptBody, request: Request) -> dict[str, Any]:
    receipt = Receipt(**body.model_dump())
    created = request.app.state.receipt_store.create(receipt)
    return asdict(created)


@router.get("/receipts/{request_id}")
def get_receipt(request_id: str, request: Request) -> dict[str, Any]:
    receipt = request.app.state.receipt_store.get(request_id)
    if receipt is None:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return asdict(receipt)


# ── reputation ────────────────────────────────────────────────────────────────

class ReputationEventBody(BaseModel):
    subject_id: str
    event_type: str
    domain: str
    timestamp: str
    weight: float = 1.0
    evidence_ref: Optional[str] = None


@router.post("/reputation/events")
def record_reputation_event(body: ReputationEventBody, request: Request) -> dict[str, Any]:
    event = ReputationEvent(**body.model_dump())
    recorded = request.app.state.reputation_service.record_event(event)
    return asdict(recorded)


@router.get("/reputation/{subject_id}")
def get_reputation(subject_id: str, request: Request) -> dict[str, Any]:
    score = request.app.state.reputation_service.compute_score(subject_id)
    return asdict(score)


# ── normalize (cache-collapse demo) ──────────────────────────────────────────

class NormalizeBody(BaseModel):
    text: str
    domain: str = "GENERAL"
    profile: str = "GENERAL_PURPOSE"


@router.post("/normalize")
def normalize_endpoint(body: NormalizeBody) -> dict[str, Any]:
    try:
        return normalize_semantics(
            body.text,
            domain=body.domain,
            profile=body.profile,
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
