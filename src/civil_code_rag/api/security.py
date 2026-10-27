"""API-key authentication that maps each key to a named client for auditing."""

import hmac
from typing import Annotated

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from pydantic import SecretStr

from civil_code_rag.config import Settings, get_settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
ANONYMOUS_CLIENT = "anonymous"


def match_client(api_key: str | None, api_keys: dict[str, SecretStr]) -> str | None:
    """Return the client ID for a key, comparing every entry in constant time."""

    if not api_key:
        return None
    candidate = api_key.encode("utf-8")
    matched = None
    for client_id, secret in api_keys.items():
        if hmac.compare_digest(candidate, secret.get_secret_value().encode("utf-8")):
            matched = client_id
    return matched


def require_client(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    api_key: Annotated[str | None, Security(API_KEY_HEADER)] = None,
) -> str:
    """Authenticate the caller and record the client ID for the audit log."""

    audit = request.state.audit
    if settings.auth_disabled:
        audit["client_id"] = ANONYMOUS_CLIENT
        return ANONYMOUS_CLIENT
    if not settings.api_keys:
        audit["outcome"] = "auth_not_configured"
        raise HTTPException(503, "API authentication is not configured.")
    client_id = match_client(api_key, settings.api_keys)
    if client_id is None:
        audit["outcome"] = "unauthorized"
        raise HTTPException(
            401, "Missing or invalid API key.", headers={"WWW-Authenticate": "ApiKey"}
        )
    audit["client_id"] = client_id
    return client_id
