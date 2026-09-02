"""Coordinator: poll the public IP and keep the mijn.host A record in sync."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import (
    MijnHostAuthError,
    MijnHostClient,
    MijnHostError,
    PublicIpError,
    fetch_public_ipv4,
)
from .const import (
    CONF_CUSTOM_IP_URL,
    CONF_DNS_DOMAIN,
    CONF_IP_SOURCE,
    CONF_RECORD_NAME,
    CONF_TTL,
    CONF_UPDATE_INTERVAL,
    DEFAULT_IP_SOURCE,
    DEFAULT_TTL,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    IP_SOURCE_CUSTOM,
    IP_SOURCES,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class MijnHostData:
    """State shared with the entities."""

    public_ip: str
    record_ip: str | None
    in_sync: bool
    last_synced: datetime | None


class MijnHostCoordinator(DataUpdateCoordinator[MijnHostData]):
    """Poll the public IP and update the mijn.host A record when it drifts."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        interval = int(
            entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_MINUTES)
        )
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} {entry.data[CONF_RECORD_NAME]}",
            config_entry=entry,
            update_interval=timedelta(minutes=interval),
        )
        self.dns_domain: str = entry.data[CONF_DNS_DOMAIN]
        self.record_name: str = entry.data[CONF_RECORD_NAME].rstrip(".").lower()
        self.client = MijnHostClient(
            async_get_clientsession(hass), entry.data[CONF_API_KEY]
        )
        self.last_synced: datetime | None = None

    @property
    def _ttl(self) -> int:
        return int(self.config_entry.options.get(CONF_TTL, DEFAULT_TTL))

    @property
    def _ip_url(self) -> str:
        source = self.config_entry.options.get(CONF_IP_SOURCE, DEFAULT_IP_SOURCE)
        if source == IP_SOURCE_CUSTOM:
            return str(self.config_entry.options.get(CONF_CUSTOM_IP_URL, ""))
        return IP_SOURCES[source][1]

    async def _async_update_data(self) -> MijnHostData:
        session = async_get_clientsession(self.hass)
        try:
            public_ip = await fetch_public_ipv4(session, self._ip_url)
        except PublicIpError as err:
            raise UpdateFailed(str(err)) from err

        try:
            records = await self.client.get_records(self.dns_domain)
        except MijnHostAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except MijnHostError as err:
            raise UpdateFailed(str(err)) from err

        record_ip: str | None = None
        for record in records:
            name = str(record.get("name", "")).rstrip(".").lower()
            if record.get("type") == "A" and name == self.record_name:
                record_ip = record.get("value")
                break

        if record_ip != public_ip:
            payload = {
                "type": "A",
                "name": f"{self.record_name}.",
                "value": public_ip,
                "ttl": self._ttl,
            }
            try:
                await self.client.update_record(self.dns_domain, payload)
            except MijnHostAuthError as err:
                raise ConfigEntryAuthFailed(str(err)) from err
            except MijnHostError as err:
                if record_ip is None:
                    raise UpdateFailed(
                        f"No A record named {self.record_name} exists and creating it"
                        f" failed; create it once in the mijn.host DNS panel ({err})"
                    ) from err
                raise UpdateFailed(str(err)) from err
            _LOGGER.info(
                "Updated A record %s: %s -> %s", self.record_name, record_ip, public_ip
            )
            self.last_synced = dt_util.utcnow()
            record_ip = public_ip

        return MijnHostData(
            public_ip=public_ip,
            record_ip=record_ip,
            in_sync=record_ip == public_ip,
            last_synced=self.last_synced,
        )
