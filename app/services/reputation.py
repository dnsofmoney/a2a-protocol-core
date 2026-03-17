from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


POSITIVE_EVENTS = [
    "CONSISTENT_SUCCESSFUL_EXECUTION",
    "LOW_DISPUTE_RATE",
    "HIGH_VERIFICATION_MATCH_RATE",
    "TIMELY_SETTLEMENT",
    "STABLE_UPTIME",
    "AUDIT_PASSED",
]

NEGATIVE_EVENTS = [
    "TASK_FAILURE",
    "FALSE_CAPABILITY_DECLARATION",
    "INVALID_SIGNATURE",
    "SETTLEMENT_DEFAULT",
    "DISPUTE_LOSS",
    "POLICY_VIOLATION",
    "REPLAY_BEHAVIOR",
]

_SUSPEND_EVENTS = {"INVALID_SIGNATURE", "POLICY_VIOLATION"}


@dataclass
class ReputationEvent:
    subject_id: str
    event_type: str
    domain: str
    timestamp: str
    weight: float = 1.0
    evidence_ref: Optional[str] = None


@dataclass
class ReputationScore:
    subject_id: str
    reliability_score: float
    performance_score: float
    integrity_score: float
    policy_compliance_score: float
    economic_score: float
    security_score: float
    last_updated: str
    trust_class: str


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


class ReputationService:
    def __init__(self) -> None:
        self._events: dict[str, list[ReputationEvent]] = {}

    def record_event(self, event: ReputationEvent) -> ReputationEvent:
        self._events.setdefault(event.subject_id, []).append(event)
        return event

    def compute_score(self, subject_id: str) -> ReputationScore:
        events = self._events.get(subject_id, [])

        # Check for suspension trigger events
        for ev in events:
            if ev.event_type in _SUSPEND_EVENTS:
                now = datetime.now(timezone.utc).isoformat()
                return ReputationScore(
                    subject_id=subject_id,
                    reliability_score=0.0,
                    performance_score=0.0,
                    integrity_score=0.0,
                    policy_compliance_score=0.0,
                    economic_score=0.0,
                    security_score=0.0,
                    last_updated=now,
                    trust_class="SUSPENDED",
                )

        # Score dimensions — start at 1.0, decay on negatives, boost on positives
        # Mapping of event_type -> dimension(s) affected
        DIMENSION_MAP: dict[str, list[str]] = {
            "CONSISTENT_SUCCESSFUL_EXECUTION": ["reliability", "performance"],
            "LOW_DISPUTE_RATE": ["reliability", "policy_compliance"],
            "HIGH_VERIFICATION_MATCH_RATE": ["integrity", "performance"],
            "TIMELY_SETTLEMENT": ["economic", "performance"],
            "STABLE_UPTIME": ["reliability"],
            "AUDIT_PASSED": ["integrity", "policy_compliance", "security"],
            "TASK_FAILURE": ["reliability", "performance"],
            "FALSE_CAPABILITY_DECLARATION": ["integrity"],
            "INVALID_SIGNATURE": ["security", "integrity"],
            "SETTLEMENT_DEFAULT": ["economic"],
            "DISPUTE_LOSS": ["policy_compliance", "economic"],
            "POLICY_VIOLATION": ["policy_compliance", "integrity"],
            "REPLAY_BEHAVIOR": ["security"],
        }

        dim_scores: dict[str, float] = {
            "reliability": 1.0,
            "performance": 1.0,
            "integrity": 1.0,
            "policy_compliance": 1.0,
            "economic": 1.0,
            "security": 1.0,
        }

        for ev in events:
            dims = DIMENSION_MAP.get(ev.event_type, [])
            delta = 0.05 * ev.weight
            if ev.event_type in POSITIVE_EVENTS:
                for d in dims:
                    dim_scores[d] = _clamp(dim_scores[d] + delta)
            elif ev.event_type in NEGATIVE_EVENTS:
                for d in dims:
                    dim_scores[d] = _clamp(dim_scores[d] - delta)

        scores = [
            dim_scores["reliability"],
            dim_scores["performance"],
            dim_scores["integrity"],
            dim_scores["policy_compliance"],
            dim_scores["economic"],
            dim_scores["security"],
        ]

        now = datetime.now(timezone.utc).isoformat()
        if all(s >= 0.95 for s in scores):
            trust_class = "A"
        elif all(s >= 0.80 for s in scores):
            trust_class = "B"
        elif all(s >= 0.60 for s in scores):
            trust_class = "C"
        else:
            trust_class = "RESTRICTED"

        return ReputationScore(
            subject_id=subject_id,
            reliability_score=round(dim_scores["reliability"], 6),
            performance_score=round(dim_scores["performance"], 6),
            integrity_score=round(dim_scores["integrity"], 6),
            policy_compliance_score=round(dim_scores["policy_compliance"], 6),
            economic_score=round(dim_scores["economic"], 6),
            security_score=round(dim_scores["security"], 6),
            last_updated=now,
            trust_class=trust_class,
        )

    def get_score(self, subject_id: str) -> Optional[ReputationScore]:
        if subject_id not in self._events:
            return None
        return self.compute_score(subject_id)

    def list_events(self, subject_id: str) -> list[ReputationEvent]:
        return self._events.get(subject_id, [])
