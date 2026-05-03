"""
A2A-042 bridge: closed AP2 PaymentMandate → A2A-041 Payment Hook.

Verification responsibilities split as follows:
  - Mandate signature / VC validation: stubbed here. Production deployments
    MUST replace `verify_mandate()` with AP2's real verifier
    (see ap2.sdk.verify in google-agentic-commerce/AP2).
  - Field-shape, expiry, amount, alias presence: enforced here.
  - Resolution + rail selection + settlement: delegated to A2A-041.

Idempotency: composite key is (transaction_id, payment_mandate_id).
A bridge MUST refuse to re-process an already-settled mandate.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.bridges.ap2.models import BridgeResult, PaymentMandate

# In-memory idempotency tracker. Production: persist to DB.
_settled_mandates: set[tuple[str, str]] = set()


def verify_mandate(mandate: PaymentMandate) -> tuple[bool, str | None]:
    """
    Verify a closed AP2 PaymentMandate.

    This is a structural verifier suitable for the reference implementation.
    Production MUST replace this with AP2's signature/VC verification.
    Returns (ok, reason). reason is None when ok is True.
    """
    contents = mandate.payment_mandate_contents

    # 1. Required fields present (Pydantic already enforces, but be explicit)
    if not contents.payment_mandate_id or not contents.transaction_id:
        return False, "MANDATE_MISSING_IDS"

    # 2. Expiry in the future
    try:
        expiry = datetime.fromisoformat(contents.expiry.replace("Z", "+00:00"))
    except ValueError:
        return False, "MANDATE_EXPIRY_INVALID_FORMAT"
    if expiry <= datetime.now(timezone.utc):
        return False, "MANDATE_EXPIRED"

    # 3. Amount looks like a positive decimal string
    try:
        amount_val = float(contents.amount)
    except ValueError:
        return False, "MANDATE_AMOUNT_INVALID"
    if amount_val <= 0:
        return False, "MANDATE_AMOUNT_NON_POSITIVE"

    # 4. Production-only checks would go here:
    #    - Verify user_authorization VC signature
    #    - Verify cart_mandate_hash matches bound cart
    #    - Verify amount matches cart total byte-for-byte
    #    - Verify currency matches resolved rail capability

    return True, None


def extract_payee_alias(mandate: PaymentMandate) -> str | None:
    """Pull merchant_payment_alias from the bound cart, if present."""
    if mandate.bound_cart is None:
        return None
    return mandate.bound_cart.contents.merchant_payment_alias


def mandate_already_settled(mandate: PaymentMandate) -> bool:
    """Idempotency check — same (transaction_id, mandate_id) twice."""
    contents = mandate.payment_mandate_contents
    return (contents.transaction_id, contents.payment_mandate_id) in _settled_mandates


def mark_mandate_settled(mandate: PaymentMandate) -> None:
    contents = mandate.payment_mandate_contents
    _settled_mandates.add((contents.transaction_id, contents.payment_mandate_id))


def reset_settled_mandates_for_test() -> None:
    """Test-only helper to clear the in-memory idempotency tracker."""
    _settled_mandates.clear()


def bridge_mandate_to_hook(
    mandate: PaymentMandate,
    *,
    payment_hook_caller,
) -> BridgeResult:
    """
    Run the full A2A-042 bridge:
      verify → extract alias → idempotency check → invoke A2A-041 hook.

    `payment_hook_caller` is a callable that takes a hook body dict and returns
    the hook response dict. In tests this is wrapped around the FastAPI test
    client; in production it points at the real A2A-041 endpoint.
    """
    contents = mandate.payment_mandate_contents

    # 1. Verify
    ok, reason = verify_mandate(mandate)
    if not ok:
        return BridgeResult(
            mandate_id=contents.payment_mandate_id,
            transaction_id=contents.transaction_id,
            bridge_status="REJECTED",
            rejection_reason=reason,
        )

    # 2. Extract alias
    alias = extract_payee_alias(mandate)
    if alias is None:
        return BridgeResult(
            mandate_id=contents.payment_mandate_id,
            transaction_id=contents.transaction_id,
            bridge_status="REJECTED",
            rejection_reason="MANDATE_NO_PAYMENT_ALIAS",
        )

    # 3. Idempotency
    if mandate_already_settled(mandate):
        return BridgeResult(
            mandate_id=contents.payment_mandate_id,
            transaction_id=contents.transaction_id,
            bridge_status="REJECTED",
            rejection_reason="MANDATE_ALREADY_SETTLED",
        )

    # 4. Invoke A2A-041
    hook_body: dict[str, Any] = {
        "task_id": contents.transaction_id,
        "agent_id": contents.agent_identifier,
        "payee_alias": alias,
        "amount": contents.amount,
        "currency": contents.currency,
    }
    hook_response = payment_hook_caller(hook_body)

    # 5. Mark settled and return
    mark_mandate_settled(mandate)
    return BridgeResult(
        mandate_id=contents.payment_mandate_id,
        transaction_id=contents.transaction_id,
        bridge_status="BRIDGED",
        hook_response=hook_response,
    )
