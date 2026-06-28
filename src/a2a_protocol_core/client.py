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

from a2a_protocol_core.schemas import (
    A2ACapabilities,
    A2APaymentHookRequest,
    A2APaymentHookResponse,
)

DEFAULT_TIMEOUT = 30


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

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def capabilities(self) -> A2ACapabilities:
        """Fetch the server's advertised A2A capabilities."""
        resp = self._session.get(
            f"{self.base_url}/v1/a2a/capabilities",
            headers=self._headers(),
            verify=self.verify_ssl,
            timeout=self.timeout,
        )
        resp.raise_for_status()
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
        resp = self._session.post(
            f"{self.base_url}/v1/a2a/payment-hook",
            data=request.model_dump_json(),
            headers=self._headers(),
            verify=self.verify_ssl,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return A2APaymentHookResponse.model_validate(resp.json())
