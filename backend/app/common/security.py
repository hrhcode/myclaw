import os
from typing import Optional

from fastapi import Header, HTTPException, status


def _read_configured_token() -> Optional[str]:
    token = os.getenv("MYCLAW_API_TOKEN")
    if token:
        return token.strip()
    return None


def _extract_token(authorization: Optional[str], x_api_key: Optional[str]) -> Optional[str]:
    if authorization:
        value = authorization.strip()
        if value.lower().startswith("bearer "):
            token = value[7:].strip()
            if token:
                return token
    if x_api_key:
        token = x_api_key.strip()
        if token:
            return token
    return None


async def require_api_auth(
    authorization: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
) -> None:
    expected = _read_configured_token()
    if not expected:
        return

    provided = _extract_token(authorization, x_api_key)
    if not provided or provided != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
