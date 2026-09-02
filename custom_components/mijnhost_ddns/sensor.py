"""Sensors for mijn.host DDNS."""

from __future__ import annotations

from datetime import datetime

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
            LastSyncedSensor(coordinator),
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


class LastSyncedSensor(MijnHostEntity, SensorEntity):
    """When this integration last rewrote the record (since HA start)."""

    _attr_translation_key = "last_synced"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    suffix = "last_synced"

    @property
    def native_value(self) -> datetime | None:
        return self.coordinator.data.last_synced
