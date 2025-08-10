import asyncio
from typing import Any, Optional

import httpx


_client: Optional[httpx.AsyncClient] = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        timeout = httpx.Timeout(connect=5.0, read=20.0, write=10.0, pool=5.0)
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
        _client = httpx.AsyncClient(http1=True, timeout=timeout, limits=limits)
    return _client


async def close_client() -> None:
    global _client
    if _client is not None:
        try:
            await _client.aclose()
        finally:
            _client = None


async def request_json(
    method: str,
    url: str,
    *,
    retries: int = 2,
    backoff: float = 0.25,
    **kwargs: Any,
) -> Any:
    """HTTP JSON helper with simple retry/backoff using a shared client."""
    last_exc: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            client = get_client()
            resp = await client.request(method, url, **kwargs)
            resp.raise_for_status()
            ct = resp.headers.get("content-type", "")
            if "application/json" in ct or resp.text.strip().startswith("{"):
                return resp.json()
            return resp.text
        except Exception as e:
            last_exc = e
            if attempt >= retries:
                break
            await asyncio.sleep(backoff * (2 ** attempt))
    assert last_exc is not None
    raise last_exc


async def get_json(url: str, **kwargs: Any) -> Any:
    return await request_json("GET", url, **kwargs)


async def post_json(url: str, **kwargs: Any) -> Any:
    return await request_json("POST", url, **kwargs)
