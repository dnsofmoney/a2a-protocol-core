from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional

from app.core.signing import sign_record, verify_record


@dataclass
class RailEndpoint:
    rail: str
    currency: str
    address: str
    settle_seconds: int
    fee_bps: int


@dataclass
class ResolutionRecord:
    alias: str
    entity: str
    preferred_rail: str
    endpoints: list[RailEndpoint]
    iso_hint: str
    ttl_seconds: int
    resolved_at: str
    signature: str
    resolver_authority: str = "A2A-031-FAS"


def _record_signable(record: ResolutionRecord) -> dict:
    return {
        "alias": record.alias,
        "entity": record.entity,
        "preferred_rail": record.preferred_rail,
        "endpoints": [asdict(e) for e in record.endpoints],
        "iso_hint": record.iso_hint,
        "ttl_seconds": record.ttl_seconds,
        "resolved_at": record.resolved_at,
        "resolver_authority": record.resolver_authority,
    }


class FASResolver:
    def __init__(self) -> None:
        self._store: dict[str, ResolutionRecord] = {}
        self._seed()

    def _seed(self) -> None:
        self.register_alias(
            alias="pay:agent.compute",
            entity="AGT-COMPUTE-001",
            endpoints=[
                RailEndpoint(rail="XRPL", currency="USD",
                             address="rComputeAgent001",
                             settle_seconds=4, fee_bps=1),
                RailEndpoint(rail="FEDNOW", currency="USD",
                             address="acct://fednow/compute",
                             settle_seconds=3, fee_bps=2),
            ],
            preferred_rail="XRPL",
        )
        self.register_alias(
            alias="pay:vendor.alpha",
            entity="VENDOR-ALPHA-001",
            endpoints=[
                RailEndpoint(rail="FEDNOW", currency="USD",
                             address="acct://fednow/vendor-alpha",
                             settle_seconds=3, fee_bps=2),
                RailEndpoint(rail="ACH", currency="USD",
                             address="acct://ach/vendor-alpha",
                             settle_seconds=86400, fee_bps=0),
            ],
            preferred_rail="FEDNOW",
        )
        self.register_alias(
            alias="pay:agent.analysis",
            entity="AGT-ANALYSIS-001",
            endpoints=[
                RailEndpoint(rail="INTERNAL_LEDGER", currency="USD",
                             address="ledger://analysis-001",
                             settle_seconds=1, fee_bps=0),
            ],
            preferred_rail="INTERNAL_LEDGER",
        )

    def register_alias(
        self,
        alias: str,
        entity: str,
        endpoints: list[RailEndpoint],
        preferred_rail: str,
        iso_hint: str = "pacs.008.001.08",
        ttl_seconds: int = 300,
    ) -> ResolutionRecord:
        resolved_at = datetime.now(timezone.utc).isoformat()
        record = ResolutionRecord(
            alias=alias,
            entity=entity,
            preferred_rail=preferred_rail,
            endpoints=endpoints,
            iso_hint=iso_hint,
            ttl_seconds=ttl_seconds,
            resolved_at=resolved_at,
            signature="",
            resolver_authority="A2A-031-FAS",
        )
        sig = sign_record(_record_signable(record))
        record.signature = sig
        self._store[alias] = record
        return record

    def resolve(self, alias: str) -> Optional[ResolutionRecord]:
        return self._store.get(alias)

    def verify(self, record: ResolutionRecord) -> bool:
        return verify_record(_record_signable(record), record.signature)

    def select_rail(
        self,
        record: ResolutionRecord,
        policy: Optional[dict] = None,
    ) -> RailEndpoint:
        if policy and "allowed_rails" in policy:
            allowed = policy["allowed_rails"]
            for ep in record.endpoints:
                if ep.rail in allowed:
                    return ep
        for ep in record.endpoints:
            if ep.rail == record.preferred_rail:
                return ep
        return record.endpoints[0]
