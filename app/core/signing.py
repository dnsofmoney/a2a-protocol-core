import hashlib, hmac, json
from typing import Any

_DEFAULT_SECRET = "a2a-dev-secret-replace-in-production"

def _record_bytes(record: dict[str, Any]) -> bytes:
    return json.dumps(record, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")

def sign_record(record: dict[str, Any],
                secret: str = _DEFAULT_SECRET) -> str:
    return hmac.new(
        secret.encode("utf-8"), _record_bytes(record), hashlib.sha256
    ).hexdigest()

def verify_record(record: dict[str, Any], signature: str,
                  secret: str = _DEFAULT_SECRET) -> bool:
    expected = sign_record(record, secret)
    return hmac.compare_digest(expected, signature)
