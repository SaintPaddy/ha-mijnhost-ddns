"""Sensors for mijn.host DDNS."""

from __future__ import annotations

from datetime import date, datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import MijnHostConfigEntry
from .entity import MijnHostEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MijnHostConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [
            PublicIpSensor(coordinator),
            RecordIpSensor(coordinator),
            RecordFqdnSensor(coordinator),
            LastSyncedSensor(coordinator),
            LastCheckedSensor(coordinator),
            KeyExpirySensor(coordinator),
        ]
    )


class PublicIpSensor(MijnHostEntity, SensorEntity):
    """The public IPv4 as reported by the lookup service."""

    _attr_translation_key = "public_ip"
    _attr_icon = "mdi:ip-outline"
    suffix = "public_ip"

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.public_ip


class RecordIpSensor(MijnHostEntity, SensorEntity):
    """The value the mijn.host A record currently holds."""

    _attr_translation_key = "record_ip"
    _attr_icon = "mdi:dns"
    suffix = "record_ip"

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.record_ip


class RecordFqdnSensor(MijnHostEntity, SensorEntity):
    """The fully qualified domain name this entry creates/maintains."""

    _attr_translation_key = "record_fqdn"
    _attr_icon = "mdi:web"
    suffix = "record_fqdn"

    @property
    def native_value(self) -> str:
        return self.coordinator.record_name

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        return {
            "dns_domain": self.coordinator.dns_domain,
            "ttl": self.coordinator.ttl,
        }


class LastSyncedSensor(MijnHostEntity, SensorEntity):
    """When this integration last rewrote the record (since HA start)."""

    _attr_translation_key = "last_synced"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    suffix = "last_synced"

    @property
    def native_value(self) -> datetime | None:
        return self.coordinator.data.last_synced


class LastCheckedSensor(MijnHostEntity, SensorEntity):
    """When the public IP and record were last successfully compared."""

    _attr_translation_key = "last_checked"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    suffix = "last_checked"

    @property
    def native_value(self) -> datetime | None:
        return self.coordinator.data.last_checked


class KeyExpirySensor(MijnHostEntity, SensorEntity):
    """User-provided expiry date of the mijn.host API key (from options)."""

    _attr_translation_key = "key_expires"
    _attr_device_class = SensorDeviceClass.DATE
    _attr_icon = "mdi:key-alert-outline"
    suffix = "key_expires"

    @property
    def native_value(self) -> date | None:
        return self.coordinator.data.key_expires_on
