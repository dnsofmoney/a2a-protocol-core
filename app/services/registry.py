from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentRecord:
    agent_id: str
    org_id: str
    domain: str
    payment_alias: Optional[str]
    endpoint: Optional[str]
    trust_tier: str
    protocol_versions: list[str]
    message_types: list[str]
    input_schemas: list[str]
    output_schemas: list[str]
    tools: list[str]
    max_latency_ms: int
    created_at: str


class AgentRegistry:
    def __init__(self) -> None:
        self._store: dict[str, AgentRecord] = {}

    def register(self, record: AgentRecord) -> AgentRecord:
        self._store[record.agent_id] = record
        return record

    def get(self, agent_id: str) -> Optional[AgentRecord]:
        return self._store.get(agent_id)

    def list_by_domain(self, domain: str) -> list[AgentRecord]:
        return [r for r in self._store.values() if r.domain == domain]

    def find_by_alias(self, payment_alias: str) -> Optional[AgentRecord]:
        for r in self._store.values():
            if r.payment_alias == payment_alias:
                return r
        return None

    def all(self) -> list[AgentRecord]:
        return list(self._store.values())
