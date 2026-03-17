from __future__ import annotations
import hashlib, json, re
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional


class SemanticNormalizationError(Exception): pass
class SemanticConfidenceError(SemanticNormalizationError): pass
class SemanticValidationError(SemanticNormalizationError): pass


class NormalizationProfile(str, Enum):
    GENERAL_PURPOSE = "GENERAL_PURPOSE"
    STRICT_FINANCIAL = "STRICT_FINANCIAL"
    STRICT_GOVERNANCE = "STRICT_GOVERNANCE"
    LOW_LATENCY = "LOW_LATENCY"
    CACHE_MAXIMIZED = "CACHE_MAXIMIZED"
    HIGH_SAFETY = "HIGH_SAFETY"


class Domain(str, Enum):
    GENERAL = "GENERAL"
    FINTECH = "FINTECH"
    COMPUTE = "COMPUTE"
    GOVERNANCE = "GOVERNANCE"
    TRUST = "TRUST"


class CanonicalAction(str, Enum):
    QUERY = "QUERY"; REPORT = "REPORT"; VERIFY = "VERIFY"; EXECUTE = "EXECUTE"
    SETTLE = "SETTLE"; RESOLVE = "RESOLVE"; REGISTER = "REGISTER"
    DISCOVER = "DISCOVER"; AUTHORIZE = "AUTHORIZE"; RESERVE = "RESERVE"
    RELEASE = "RELEASE"; ESCALATE = "ESCALATE"; REJECT = "REJECT"
    APPROVE = "APPROVE"; SCORE = "SCORE"; PROPOSE = "PROPOSE"; VOTE = "VOTE"
    ARBITRATE = "ARBITRATE"; APPEAL = "APPEAL"; ATTEST = "ATTEST"
    CACHE = "CACHE"; ROUTE = "ROUTE"; SCHEDULE = "SCHEDULE"; METER = "METER"


class CanonicalSubject(str, Enum):
    PAYMENT = "PAYMENT"; PAYMENT_ALIAS = "PAYMENT_ALIAS"; WORKLOAD = "WORKLOAD"
    AGENT = "AGENT"; RESOLUTION_RECORD = "RESOLUTION_RECORD"
    SETTLEMENT_INSTRUCTION = "SETTLEMENT_INSTRUCTION"
    REPUTATION_RECORD = "REPUTATION_RECORD"; PROPOSAL = "PROPOSAL"
    DISPUTE_CASE = "DISPUTE_CASE"; POLICY = "POLICY"; RECEIPT = "RECEIPT"
    SCHEMA = "SCHEMA"; CONTAINER_JOB = "CONTAINER_JOB"
    RESOURCE_CLASS = "RESOURCE_CLASS"; BID = "BID"; SERVICE_OFFER = "SERVICE_OFFER"


PROFILE_MIN_CONFIDENCE: dict[NormalizationProfile, float] = {
    NormalizationProfile.GENERAL_PURPOSE: 0.50,
    NormalizationProfile.LOW_LATENCY: 0.45,
    NormalizationProfile.CACHE_MAXIMIZED: 0.45,
    NormalizationProfile.STRICT_FINANCIAL: 0.90,
    NormalizationProfile.STRICT_GOVERNANCE: 0.90,
    NormalizationProfile.HIGH_SAFETY: 0.95,
}

DEFAULT_DOMAIN_SUBJECTS: dict[Domain, CanonicalSubject] = {
    Domain.FINTECH: CanonicalSubject.PAYMENT,
    Domain.COMPUTE: CanonicalSubject.WORKLOAD,
    Domain.GOVERNANCE: CanonicalSubject.PROPOSAL,
    Domain.TRUST: CanonicalSubject.REPUTATION_RECORD,
    Domain.GENERAL: CanonicalSubject.AGENT,
}

DOMAIN_ACTION_SYNONYMS: dict[Domain, dict[str, CanonicalAction]] = {
    Domain.GENERAL: {
        "check": CanonicalAction.VERIFY,
        "review": CanonicalAction.VERIFY,
        "inspect": CanonicalAction.VERIFY,
        "look up": CanonicalAction.QUERY,
        "lookup": CanonicalAction.QUERY,
        "find": CanonicalAction.QUERY,
        "discover": CanonicalAction.DISCOVER,
        "register": CanonicalAction.REGISTER,
        "report": CanonicalAction.REPORT,
        "send": CanonicalAction.EXECUTE,
        "execute": CanonicalAction.EXECUTE,
        "run": CanonicalAction.EXECUTE,
    },
    Domain.FINTECH: {
        "pay": CanonicalAction.SETTLE,
        "send": CanonicalAction.SETTLE,
        "transfer": CanonicalAction.SETTLE,
        "settle": CanonicalAction.SETTLE,
        "authorize": CanonicalAction.AUTHORIZE,
        "reserve": CanonicalAction.RESERVE,
        "release": CanonicalAction.RELEASE,
        "resolve": CanonicalAction.RESOLVE,
        "find": CanonicalAction.RESOLVE,
        "lookup": CanonicalAction.RESOLVE,
        "check": CanonicalAction.VERIFY,
        "review": CanonicalAction.VERIFY,
    },
    Domain.COMPUTE: {
        "run": CanonicalAction.EXECUTE,
        "launch": CanonicalAction.EXECUTE,
        "execute": CanonicalAction.EXECUTE,
        "schedule": CanonicalAction.SCHEDULE,
        "meter": CanonicalAction.METER,
        "check": CanonicalAction.VERIFY,
        "review": CanonicalAction.VERIFY,
        "cache": CanonicalAction.CACHE,
    },
    Domain.GOVERNANCE: {
        "propose": CanonicalAction.PROPOSE,
        "vote": CanonicalAction.VOTE,
        "appeal": CanonicalAction.APPEAL,
        "arbitrate": CanonicalAction.ARBITRATE,
        "dispute": CanonicalAction.ARBITRATE,
        "reject": CanonicalAction.REJECT,
        "approve": CanonicalAction.APPROVE,
    },
    Domain.TRUST: {
        "score": CanonicalAction.SCORE,
        "rate": CanonicalAction.SCORE,
        "attest": CanonicalAction.ATTEST,
        "verify": CanonicalAction.VERIFY,
        "check": CanonicalAction.VERIFY,
    },
}

DOMAIN_SUBJECT_KEYWORDS: dict[Domain, dict[str, CanonicalSubject]] = {
    Domain.FINTECH: {
        "payment alias": CanonicalSubject.PAYMENT_ALIAS,
        "alias": CanonicalSubject.PAYMENT_ALIAS,
        "payment": CanonicalSubject.PAYMENT,
        "settlement": CanonicalSubject.SETTLEMENT_INSTRUCTION,
        "resolution": CanonicalSubject.RESOLUTION_RECORD,
    },
    Domain.COMPUTE: {
        "workload": CanonicalSubject.WORKLOAD,
        "container job": CanonicalSubject.CONTAINER_JOB,
        "container": CanonicalSubject.CONTAINER_JOB,
        "resource": CanonicalSubject.RESOURCE_CLASS,
        "bid": CanonicalSubject.BID,
    },
    Domain.GOVERNANCE: {
        "proposal": CanonicalSubject.PROPOSAL,
        "dispute": CanonicalSubject.DISPUTE_CASE,
        "policy": CanonicalSubject.POLICY,
        "receipt": CanonicalSubject.RECEIPT,
    },
    Domain.TRUST: {
        "reputation": CanonicalSubject.REPUTATION_RECORD,
        "agent": CanonicalSubject.REPUTATION_RECORD,
    },
    Domain.GENERAL: {
        "agent": CanonicalSubject.AGENT,
        "schema": CanonicalSubject.SCHEMA,
        "service": CanonicalSubject.SERVICE_OFFER,
    },
}

CONFIDENCE_WEIGHTS: dict[Domain, tuple[float, float, float]] = {
    Domain.FINTECH:    (0.40, 0.30, 0.30),
    Domain.GOVERNANCE: (0.40, 0.35, 0.25),
    Domain.COMPUTE:    (0.35, 0.30, 0.35),
    Domain.TRUST:      (0.35, 0.35, 0.30),
    Domain.GENERAL:    (0.34, 0.33, 0.33),
}


@dataclass(slots=True)
class TransformationTrace:
    raw_expression: str
    interpreted_action: Optional[str] = None
    interpreted_subject: Optional[str] = None
    rules_applied: list[str] = field(default_factory=list)
    semantic_version: str = "1.0"


@dataclass(slots=True)
class CanonicalSemanticForm:
    semantic_version: str
    normalization_profile: str
    domain: str
    action: str
    subject: str
    object: str
    qualifiers: dict[str, Any] = field(default_factory=dict)
    constraints: dict[str, Any] = field(default_factory=dict)
    references: dict[str, Any] = field(default_factory=dict)
    semantic_confidence: float = 0.0
    trace: Optional[TransformationTrace] = None

    def to_dict(self, include_trace: bool = False) -> dict[str, Any]:
        out = {
            "semantic_version": self.semantic_version,
            "normalization_profile": self.normalization_profile,
            "domain": self.domain,
            "action": self.action,
            "subject": self.subject,
            "object": self.object,
            "qualifiers": self.qualifiers,
            "constraints": self.constraints,
            "references": self.references,
            "semantic_confidence": round(self.semantic_confidence, 6),
        }
        if include_trace and self.trace:
            out["trace"] = asdict(self.trace)
        return out

    def canonical_json(self) -> str:
        return json.dumps(self.to_dict(include_trace=False),
                          sort_keys=True, separators=(",", ":"))

    def _cache_maximized_json(self) -> str:
        """For CACHE_MAXIMIZED profile: hash only core semantic identity fields."""
        core = {
            "semantic_version": self.semantic_version,
            "normalization_profile": self.normalization_profile,
            "domain": self.domain,
            "action": self.action,
            "subject": self.subject,
            "object": self.object,
        }
        return json.dumps(core, sort_keys=True, separators=(",", ":"))

    def semantic_hash(self) -> str:
        if self.normalization_profile == NormalizationProfile.CACHE_MAXIMIZED.value:
            payload = self._cache_maximized_json()
        else:
            payload = self.canonical_json()
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class SemanticNormalizer:
    """A2A-009 compliant semantic normalizer."""

    def __init__(
        self,
        semantic_version: str = "1.0",
        profile: NormalizationProfile = NormalizationProfile.GENERAL_PURPOSE,
    ) -> None:
        self.semantic_version = semantic_version
        self.profile = profile

    def normalize(
        self,
        raw_input: str,
        *,
        domain: Domain = Domain.GENERAL,
        explicit_object: Optional[str] = None,
        qualifiers: Optional[dict[str, Any]] = None,
        constraints: Optional[dict[str, Any]] = None,
        references: Optional[dict[str, Any]] = None,
        require_min_confidence: bool = True,
    ) -> CanonicalSemanticForm:
        text = self._clean(raw_input)
        trace = TransformationTrace(raw_expression=raw_input)

        action, action_conf, action_rule = self._infer_action(text, domain)
        if action is None:
            raise SemanticValidationError("SEMANTIC_ACTION_MISSING")
        trace.interpreted_action = action.value
        trace.rules_applied.append(action_rule)

        subject, subject_conf, subject_rule = self._infer_subject(text, domain)
        if subject is None:
            subject = DEFAULT_DOMAIN_SUBJECTS[domain]
            subject_conf = 0.50
            subject_rule = f"default_subject:{domain.value}"
        trace.interpreted_subject = subject.value
        trace.rules_applied.append(subject_rule)

        obj, object_conf, obj_rules, extracted = \
            self._infer_object_and_qualifiers(text, domain, subject,
                                              explicit_object=explicit_object)
        trace.rules_applied.extend(obj_rules)

        merged_qualifiers: dict[str, Any] = {}
        merged_qualifiers.update(extracted.get("qualifiers", {}))
        if qualifiers:
            merged_qualifiers.update(qualifiers)

        merged_references: dict[str, Any] = {}
        merged_references.update(extracted.get("references", {}))
        if references:
            merged_references.update(references)

        merged_constraints = dict(constraints) if constraints else {}

        confidence = self._score_confidence(
            action_conf, subject_conf, object_conf, domain
        )

        min_conf = PROFILE_MIN_CONFIDENCE[self.profile]
        if require_min_confidence and confidence < min_conf:
            raise SemanticConfidenceError(
                f"SEMANTIC_CONFIDENCE_TOO_LOW: {confidence:.3f} < {min_conf:.3f}"
            )

        form = CanonicalSemanticForm(
            semantic_version=self.semantic_version,
            normalization_profile=self.profile.value,
            domain=domain.value,
            action=action.value,
            subject=subject.value,
            object=obj,
            qualifiers=dict(sorted(merged_qualifiers.items())),
            constraints=dict(sorted(merged_constraints.items())),
            references=dict(sorted(merged_references.items())),
            semantic_confidence=confidence,
            trace=trace,
        )
        self._validate_form(form)
        return form

    def normalize_and_hash(
        self, raw_input: str, **kwargs: Any
    ) -> tuple[CanonicalSemanticForm, str]:
        form = self.normalize(raw_input, **kwargs)
        return form, form.semantic_hash()

    # ── private ──────────────────────────────────────────────────────────

    def _clean(self, text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().lower())

    def _infer_action(
        self, text: str, domain: Domain
    ) -> tuple[Optional[CanonicalAction], float, str]:
        mapping: dict[str, CanonicalAction] = {}
        mapping.update(DOMAIN_ACTION_SYNONYMS.get(Domain.GENERAL, {}))
        if domain != Domain.GENERAL:
            mapping.update(DOMAIN_ACTION_SYNONYMS.get(domain, {}))
        for phrase in sorted(mapping, key=len, reverse=True):
            if re.search(rf"\b{re.escape(phrase)}\b", text):
                return mapping[phrase], 0.98, \
                    f"action_synonym:{phrase}->{mapping[phrase].value}"
        return None, 0.0, "action_unresolved"

    def _infer_subject(
        self, text: str, domain: Domain
    ) -> tuple[Optional[CanonicalSubject], float, str]:
        mapping: dict[str, CanonicalSubject] = {}
        # Load GENERAL first so domain-specific keywords take priority
        mapping.update(DOMAIN_SUBJECT_KEYWORDS.get(Domain.GENERAL, {}))
        if domain != Domain.GENERAL:
            mapping.update(DOMAIN_SUBJECT_KEYWORDS.get(domain, {}))
        for phrase in sorted(mapping, key=len, reverse=True):
            if re.search(rf"\b{re.escape(phrase)}\b", text):
                return mapping[phrase], 0.95, \
                    f"subject_keyword:{phrase}->{mapping[phrase].value}"
        return None, 0.0, "subject_unresolved"

    def _infer_object_and_qualifiers(
        self,
        text: str,
        domain: Domain,
        subject: CanonicalSubject,
        *,
        explicit_object: Optional[str] = None,
    ) -> tuple[str, float, list[str], dict[str, dict[str, Any]]]:
        qualifiers: dict[str, Any] = {}
        refs: dict[str, Any] = {}
        rules: list[str] = []

        if explicit_object:
            obj, obj_conf = explicit_object, 0.99
            rules.append("object:explicit")
        else:
            obj, obj_conf, obj_rule = self._infer_object(text, domain, subject)
            rules.append(obj_rule)

        amount = self._extract_amount(text)
        if amount is not None:
            qualifiers["amount"] = amount
            rules.append("qualifier:amount")

        currency = self._extract_currency(text)
        if currency is not None:
            qualifiers["currency"] = currency
            rules.append("qualifier:currency")

        alias = self._extract_payment_alias(text)
        if alias:
            refs["payment_alias"] = alias
            if not explicit_object and subject == CanonicalSubject.PAYMENT_ALIAS:
                obj, obj_conf = alias, 0.95
                rules.append("object:payment_alias")
            else:
                rules.append("reference:payment_alias")

        agent_id = self._extract_agent_id(text)
        if agent_id:
            refs["agent_id"] = agent_id
            if not explicit_object and subject in {
                CanonicalSubject.AGENT, CanonicalSubject.PAYMENT
            }:
                obj, obj_conf = agent_id, 0.93
                rules.append("object:agent_id")
            else:
                rules.append("reference:agent_id")

        wl_id = self._extract_workload_id(text)
        if wl_id:
            refs["workload_id"] = wl_id
            if not explicit_object and subject == CanonicalSubject.WORKLOAD:
                obj, obj_conf = wl_id, 0.93
                rules.append("object:workload_id")
            else:
                rules.append("reference:workload_id")

        return obj, obj_conf, rules, {"qualifiers": qualifiers, "references": refs}

    def _infer_object(
        self, text: str, domain: Domain, subject: CanonicalSubject
    ) -> tuple[str, float, str]:
        if subject == CanonicalSubject.PAYMENT_ALIAS:
            a = self._extract_payment_alias(text)
            if a:
                return a, 0.95, "object:payment_alias_extracted"
            return "PAYMENT_ALIAS", 0.55, "object:generic_payment_alias"
        if subject == CanonicalSubject.PAYMENT:
            aid = self._extract_agent_id(text)
            if aid:
                return aid, 0.92, "object:payment_agent_id"
            a = self._extract_payment_alias(text)
            if a:
                return a, 0.90, "object:payment_alias_target"
            if "compute" in text:
                return "AGT-COMPUTE-001", 0.72, "object:heuristic_compute"
            return "TARGET_PAYMENT_ENTITY", 0.52, "object:generic_payment"
        if subject == CanonicalSubject.WORKLOAD:
            wl = self._extract_workload_id(text)
            if wl:
                return wl, 0.92, "object:workload_id"
            if "gpu" in text or "inference" in text:
                return "WL-INFERENCE-TARGET", 0.68, "object:heuristic_workload"
            return "WORKLOAD", 0.55, "object:generic_workload"
        if subject == CanonicalSubject.PROPOSAL:
            m = re.search(r"\bproposal[-\s:]?([a-z0-9_]+)\b", text)
            if m:
                return f"PROPOSAL-{m.group(1).upper()}", 0.88, "object:proposal_id"
            return "PROPOSAL", 0.55, "object:generic_proposal"
        if subject == CanonicalSubject.DISPUTE_CASE:
            m = re.search(r"\bcase[-\s:]?([a-z0-9_]+)\b", text)
            if m:
                return f"CASE-{m.group(1).upper()}", 0.88, "object:case_id"
            return "DISPUTE_CASE", 0.55, "object:generic_dispute"
        if subject == CanonicalSubject.REPUTATION_RECORD:
            aid = self._extract_agent_id(text)
            if aid:
                return aid, 0.85, "object:reputation_agent_id"
            return "REPUTATION_RECORD", 0.55, "object:generic_reputation"
        return subject.value, 0.50, "object:default_subject_token"

    def _extract_amount(self, text: str) -> Optional[float]:
        m = re.search(r"\$\s*(\d+(?:\.\d+)?)", text)
        if m:
            return float(m.group(1))
        word_map = {
            "one": 1.0, "two": 2.0, "three": 3.0, "four": 4.0,
            "five": 5.0, "six": 6.0, "seven": 7.0, "eight": 8.0,
            "nine": 9.0, "ten": 10.0,
        }
        for word, val in word_map.items():
            if re.search(rf"\b{word}\b", text) and re.search(
                r"\b(dollar|buck|usd)\b", text
            ):
                return val
        m = re.search(r"\b(\d+(?:\.\d+)?)\b", text)
        if m and re.search(r"\b(dollar|buck|usd)\b", text):
            return float(m.group(1))
        return None

    def _extract_currency(self, text: str) -> Optional[str]:
        if re.search(r"\busdc\b", text):
            return "USDC"
        if re.search(r"\bxrp\b", text):
            return "XRP"
        if re.search(r"\b(usd|dollar|dollars|buck|bucks)\b", text) or "$" in text:
            return "USD"
        return None

    def _extract_payment_alias(self, text: str) -> Optional[str]:
        m = re.search(r"\bpay:[a-z0-9._-]+\b", text)
        return m.group(0) if m else None

    def _extract_agent_id(self, text: str) -> Optional[str]:
        m = re.search(r"\bagt-[a-z0-9_-]+\b", text, re.IGNORECASE)
        return m.group(0).upper() if m else None

    def _extract_workload_id(self, text: str) -> Optional[str]:
        m = re.search(r"\bwl-[a-z0-9_-]+\b", text, re.IGNORECASE)
        return m.group(0).upper() if m else None

    def _score_confidence(
        self,
        action_conf: float,
        subject_conf: float,
        object_conf: float,
        domain: Domain,
    ) -> float:
        wa, ws, wo = CONFIDENCE_WEIGHTS[domain]
        return round(
            action_conf * wa + subject_conf * ws + object_conf * wo, 6
        )

    def _validate_form(self, form: CanonicalSemanticForm) -> None:
        if not form.action:
            raise SemanticValidationError("SEMANTIC_ACTION_MISSING")
        if not form.subject:
            raise SemanticValidationError("SEMANTIC_SUBJECT_MISSING")
        if self.profile == NormalizationProfile.STRICT_FINANCIAL:
            allowed = {
                CanonicalSubject.PAYMENT.value,
                CanonicalSubject.PAYMENT_ALIAS.value,
                CanonicalSubject.SETTLEMENT_INSTRUCTION.value,
                CanonicalSubject.RESOLUTION_RECORD.value,
            }
            if form.subject not in allowed:
                raise SemanticValidationError(
                    "SEMANTIC_PROFILE_VIOLATION: financial subject required"
                )
        if self.profile == NormalizationProfile.STRICT_GOVERNANCE:
            allowed = {
                CanonicalAction.PROPOSE.value, CanonicalAction.VOTE.value,
                CanonicalAction.ARBITRATE.value, CanonicalAction.APPEAL.value,
                CanonicalAction.APPROVE.value, CanonicalAction.REJECT.value,
            }
            if form.action not in allowed:
                raise SemanticValidationError(
                    "SEMANTIC_PROFILE_VIOLATION: governance action required"
                )


def normalize_semantics(
    raw_input: str,
    *,
    domain: str = "GENERAL",
    profile: str = "GENERAL_PURPOSE",
    explicit_object: Optional[str] = None,
    qualifiers: Optional[dict[str, Any]] = None,
    constraints: Optional[dict[str, Any]] = None,
    references: Optional[dict[str, Any]] = None,
    require_min_confidence: bool = True,
) -> dict[str, Any]:
    """Functional entrypoint. Returns canonical dict + semantic_hash."""
    normalizer = SemanticNormalizer(profile=NormalizationProfile(profile))
    form = normalizer.normalize(
        raw_input,
        domain=Domain(domain),
        explicit_object=explicit_object,
        qualifiers=qualifiers,
        constraints=constraints,
        references=references,
        require_min_confidence=require_min_confidence,
    )
    result = form.to_dict(include_trace=True)
    result["semantic_hash"] = form.semantic_hash()
    return result
