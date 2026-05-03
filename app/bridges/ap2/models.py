"""
Minimal Pydantic models matching the public AP2 mandate shape.

These are independent reimplementations of the public AP2 data shape
documented at https://github.com/google-agentic-commerce/AP2 and the
specification at https://ap2-protocol.org. The Apache-2.0 license on
AP2 permits this. We don't import AP2's package to keep this repo
zero-dependency on Google's SDK.

The only addition over AP2's published shape is the optional
`merchant_payment_alias` field on `CartContents` — see the proposed
upstream change in our PR_PACKAGE.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CartContents(BaseModel):
    """The data merchants sign to produce a CartMandate."""

    id: str = Field(..., description="Unique identifier for this cart.")
    merchant_name: str = Field(..., description="Display name of the merchant.")
    cart_expiry: str = Field(..., description="ISO-8601 expiry timestamp.")
    amount: str = Field(..., description="Total amount, as a decimal string.")
    currency: str = Field(default="USD", description="ISO 4217 currency code.")
    merchant_payment_alias: str | None = Field(
        default=None,
        description=(
            "Optional FAS-1 financial address for the merchant in "
            "pay:<entity>.<namespace> form. When present, A2A-042 uses this "
            "alias for resolution. When absent, the bridge falls back to a "
            "registry lookup keyed on merchant_name (lower trust)."
        ),
        examples=["pay:merchant.acme"],
    )


class CartMandate(BaseModel):
    """A merchant-signed cart."""

    contents: CartContents
    merchant_authorization: str | None = Field(
        default=None,
        description="Merchant JWT signing the cart contents (AP2-defined).",
    )


class PaymentMandateContents(BaseModel):
    """The data inside a closed PaymentMandate."""

    payment_mandate_id: str = Field(..., description="Unique mandate identifier.")
    cart_mandate_hash: str = Field(..., description="Hash of the bound CartMandate.")
    transaction_id: str = Field(..., description="Merchant order / transaction reference.")
    agent_identifier: str = Field(..., description="Identifier of the executing agent.")
    amount: str = Field(..., description="Authorized amount.")
    currency: str = Field(default="USD")
    expiry: str = Field(..., description="ISO-8601 mandate expiry.")
    timestamp: str = Field(..., description="ISO-8601 mandate creation time.")


class PaymentMandate(BaseModel):
    """The closed Payment Mandate carried into the settlement layer."""

    payment_mandate_contents: PaymentMandateContents
    user_authorization: str | None = Field(
        default=None,
        description="User VC presentation signing the mandate (AP2-defined).",
    )
    # Bridge-only: the bound cart, so the bridge can extract merchant_payment_alias.
    # In a full AP2 implementation this would be looked up by cart_mandate_hash.
    bound_cart: CartMandate | None = Field(
        default=None,
        description="Optional bound CartMandate for inline bridge resolution.",
    )


class BridgeResult(BaseModel):
    """The bridge's combined response: mandate verification + A2A-041 hook."""

    mandate_id: str
    transaction_id: str
    bridge_status: str  # "BRIDGED" | "REJECTED"
    rejection_reason: str | None = None
    hook_response: dict[str, Any] | None = None
