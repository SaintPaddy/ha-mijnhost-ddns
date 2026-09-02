"""Async client for the mijn.host v2 API and public-IP lookup."""

from __future__ import annotations

import ipaddress
from typing import Any

import aiohttp

from .const import API_BASE

USER_AGENT = "ha-mijnhost-ddns (Home Assistant custom integration)"
TIMEOUT = aiohttp.ClientTimeout(total=30)


class MijnHostError(Exception):
    """Base error talking to mijn.host."""


class MijnHostAuthError(MijnHostError):
    """Invalid or revoked API key."""


class PublicIpError(Exception):
    """Public IP lookup failed."""


class MijnHostClient:
    """Minimal async client for the mijn.host v2 API."""

    def __init__(self, session: aiohttp.ClientSession, api_key: str) -> None:
        self._session = session
        self._api_key = api_key

    async def _request(
        self, method: str, path: str, json: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        headers = {
            "API-Key": self._api_key,
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }
        try:
            async with self._session.request(
                method, f"{API_BASE}{path}", json=json, headers=headers, timeout=TIMEOUT
            ) as resp:
                if resp.status in (401, 403):
                    raise MijnHostAuthError(
                        f"mijn.host rejected the API key (HTTP {resp.status})"
                    )
                body: Any = None
                if resp.content_type == "application/json":
                    body = await resp.json()
                if resp.status >= 400:
                    description = ""
                    if isinstance(body, dict):
                        description = str(body.get("status_description", ""))
                    raise MijnHostError(
                        f"mijn.host API error HTTP {resp.status} {description}".strip()
                    )
                return body if isinstance(body, dict) else {}
        except TimeoutError as err:
            raise MijnHostError("Timeout talking to mijn.host") from err
        except aiohttp.ClientError as err:
            raise MijnHostError(f"Connection error talking to mijn.host: {err}") from err

    async def get_records(self, domain: str) -> list[dict[str, Any]]:
        """Return all DNS records for a domain."""
        body = await self._request("GET", f"/domains/{domain}/dns")
        data = body.get("data") or {}
        records = data.get("records")
        if not isinstance(records, list):
            raise MijnHostError("Unexpected response from mijn.host (no records list)")
        return records

    async def update_record(self, domain: str, record: dict[str, Any]) -> None:
        """Update (or create) a single DNS record."""
        await self._request("PATCH", f"/domains/{domain}/dns", json={"record": record})


async def fetch_public_ipv4(session: aiohttp.ClientSession, url: str) -> str:
    """Fetch the current public IPv4 from a plain-text echo service."""
    try:
        async with session.get(
            url, timeout=TIMEOUT, headers={"User-Agent": USER_AGENT}
        ) as resp:
            if resp.status >= 400:
                raise PublicIpError(f"{url} returned HTTP {resp.status}")
            text = (await resp.text()).strip()
    except TimeoutError as err:
        raise PublicIpError(f"Timeout fetching public IP from {url}") from err
    except aiohttp.ClientError as err:
        raise PublicIpError(f"Connection error fetching public IP from {url}: {err}") from err

    try:
        ip = ipaddress.ip_address(text)
    except ValueError as err:
        raise PublicIpError(
            f"{url} did not return a bare IP address (got: {text[:80]!r})"
        ) from err
    if ip.version != 4:
        raise PublicIpError(
            f"{url} returned an IPv6 address ({text}); "
            "pick an IPv4-only source for A-record updates"
        )
    return str(ip)
