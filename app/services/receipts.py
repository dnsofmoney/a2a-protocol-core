from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


VALID_STATUSES = [
    "RECEIVED", "ACCEPTED", "PROCESSING", "COMPLETED", "FAILED", "ESCALATED"
]


@dataclass
class Receipt:
    request_id: str
    receipt_status: str
    receiver_agent_id: str
    timestamp: str
    payload_hash: str
    execution_ref: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class ReceiptStore:
    def __init__(self) -> None:
        self._store: dict[str, Receipt] = {}

    def create(self, receipt: Receipt) -> Receipt:
        self._store[receipt.request_id] = receipt
        return receipt

    def update_status(
        self,
        request_id: str,
        status: str,
        execution_ref: Optional[str] = None,
    ) -> Receipt:
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}")
        receipt = self._store[request_id]
        receipt.receipt_status = status
        if execution_ref is not None:
            receipt.execution_ref = execution_ref
        return receipt

    def get(self, request_id: str) -> Optional[Receipt]:
        return self._store.get(request_id)

    def list_all(self) -> list[Receipt]:
        return list(self._store.values())
