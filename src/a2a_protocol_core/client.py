"""
A2A-041 Payment Hook client.

A thin, synchronous client over the DNS of Money A2A surface. Intelligence
lives in the *calling* agent; this client only carries a well-formed,
validated request to the deterministic core and parses the response.

    from a2a_protocol_core import A2APaymentHookClient

    client = A2APaymentHookClient(base_url="https://api.dnsofmoney.com")
    result = client.trigger(
        job_id="job-123",
        provider_pay_address="pay:agent.compute",
        requester_pay_address="pay:vendor.alpha",
        amount="2.50",
        currency="USD",
        semantic_hash="abc123...",
    )
    print(result.settlement_result.status, result.iso_message_ref)
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional, Union

import requests

from a2a_protocol_core._retry import get_with_retries
from a2a_protocol_core.schemas import (
    A2ACapabilities,
    A2APaymentHookRequest,
    A2APaymentHookResponse,
)

DEFAULT_TIMEOUT = 30


class A2AClientError(RuntimeError):
    """HTTP-level failure from the A2A surface, with response context attached.

    Carries ``status_code`` and a ``body`` snippet so an agent can branch on the
    failure (409 duplicate job vs 422 validation vs 5xx) instead of parsing a
    bare ``requests.HTTPError`` string.
    """

    def __init__(self, message: str, *, status_code: Optional[int] = None, body: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class A2APaymentHookClient:
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        verify_ssl: bool = True,
        timeout: int = DEFAULT_TIMEOUT,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self._session = session or requests.Session()
        if not verify_ssl:
            # Session-wide so the retried GET honors it too (only set when the
            # caller explicitly opted out of TLS verification).
            self._session.verify = False

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def capabilities(self) -> A2ACapabilities:
        """Fetch the server's advertised A2A capabilities (idempotent — retried)."""
        resp = get_with_retries(
            self._session,
            f"{self.base_url}/v1/a2a/capabilities",
            headers=self._headers(),
            timeout=self.timeout,
        )
        if resp.status_code != 200:
            raise A2AClientError(
                f"capabilities failed {resp.status_code}: {resp.text[:300]}",
                status_code=resp.status_code,
                body=resp.text[:300],
            )
        return A2ACapabilities.model_validate(resp.json())

    def trigger(
        self,
        job_id: str,
        provider_pay_address: str,
        requester_pay_address: str,
        amount: Union[str, int, float, Decimal],
        semantic_hash: str,
        currency: str = "USD",
        receipt_ref: Optional[str] = None,
    ) -> A2APaymentHookResponse:
        """
        Fire the A2A-041 payment hook.

        The request is validated client-side (pay: URI grammar, non-empty
        semantic hash) before it ever hits the wire, so malformed intents fail
        fast and locally.
        """
        request = A2APaymentHookRequest(
            job_id=job_id,
            provider_pay_address=provider_pay_address,
            requester_pay_address=requester_pay_address,
            amount=Decimal(str(amount)),
            currency=currency,
            semantic_hash=semantic_hash,
            receipt_ref=receipt_ref,
        )
        # POST is sent exactly once — it triggers settlement, so the client never
        # auto-retries it. On a transient failure, re-send with the SAME job_id +
        # semantic_hash: the server derives its idempotency key from that pair, so
        # a duplicate returns the stored outcome instead of settling twice.
        resp = self._session.post(
            f"{self.base_url}/v1/a2a/payment-hook",
            data=request.model_dump_json(),
            headers=self._headers(),
            verify=self.verify_ssl,
            timeout=self.timeout,
        )
        if resp.status_code >= 400:
            raise A2AClientError(
                f"payment hook failed {resp.status_code}: {resp.text[:300]}",
                status_code=resp.status_code,
                body=resp.text[:300],
            )
        return A2APaymentHookResponse.model_validate(resp.json())
