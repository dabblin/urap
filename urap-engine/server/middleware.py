"""URAP Engine — request auth middleware.

API key validation via X-Api-Key header.
If URAP_API_KEY env var is unset, all requests are allowed (dev mode).
"""
import os
from fastapi import Header, HTTPException, Depends
from typing import Annotated


def get_api_key() -> str:
    return os.getenv("URAP_API_KEY", "")


async def require_api_key(
    x_api_key: Annotated[str, Header(alias="x-api-key")] = "",
    configured_key: str = Depends(get_api_key),
) -> None:
    if not configured_key:
        return  # dev mode — no key configured
    if x_api_key != configured_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
