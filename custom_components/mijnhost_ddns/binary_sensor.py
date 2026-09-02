"""Binary sensor for mijn.host DDNS."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import MijnHostConfigEntry
from .entity import MijnHostEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MijnHostConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([InSyncBinarySensor(entry.runtime_data)])


class InSyncBinarySensor(MijnHostEntity, BinarySensorEntity):
    """On when the DNS record matches the current public IP."""

    _attr_translation_key = "in_sync"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    suffix = "in_sync"

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.in_sync
