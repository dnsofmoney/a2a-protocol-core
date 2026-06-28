"""
Wire schemas for the A2A-041 Payment Hook.

Pydantic v2 models shared between client and server. These define the public
request/response contract for ``POST /v1/a2a/payment-hook``.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, field_validator

from a2a_protocol_core.addressing import is_valid_pay_uri


class A2APaymentHookRequest(BaseModel):
    """A2A-041 compute-marketplace receipt -> settlement trigger."""

    job_id: str
    provider_pay_address: str
    requester_pay_address: str
    amount: Decimal
    currency: str = "USD"
    semantic_hash: str
    receipt_ref: Optional[str] = None

    @field_validator("provider_pay_address", "requester_pay_address")
    @classmethod
    def _validate_pay_uri(cls, v: str) -> str:
        if not is_valid_pay_uri(v):
            raise ValueError(f"Invalid pay: URI format: {v}")
        return v

    @field_validator("semantic_hash")
    @classmethod
    def _validate_semantic_hash(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("semantic_hash must not be empty")
        return v


class ResolutionDetail(BaseModel):
    provider_address: Optional[str] = None
    rail: Optional[str] = None
    endpoint: Optional[str] = None


class SettlementDetail(BaseModel):
    status: str
    rail: Optional[str] = None
    tx_ref: Optional[str] = None
    amount: Decimal
    currency: str


class A2APaymentHookResponse(BaseModel):
    hook_id: uuid.UUID
    job_id: str
    resolution: ResolutionDetail
    settlement_result: SettlementDetail
    iso_message_ref: Optional[str] = None
    created_at: datetime


class A2ACapabilities(BaseModel):
    binding_version: str
    supported_schemes: list[str]
    protocol_versions: list[str]
