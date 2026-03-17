from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class SettlementInstruction:
    rail: str
    payer_id: str
    payee_address: str
    amount: float
    currency: str
    reference_id: str
    iso_hint: str = "pacs.008.001.08"


@dataclass
class SettlementResult:
    rail: str
    reference_id: str
    status: str        # SETTLED | FAILED | PENDING
    settle_time_seconds: int
    failure_reason: Optional[str] = None
    settled_at: Optional[str] = None


class RailAdapter(ABC):
    @abstractmethod
    def execute(self, instruction: SettlementInstruction) -> SettlementResult: ...

    @abstractmethod
    def capabilities(self) -> dict: ...
