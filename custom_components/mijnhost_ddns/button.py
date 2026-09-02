"""Button for mijn.host DDNS."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import MijnHostConfigEntry
from .entity import MijnHostEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MijnHostConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([SyncNowButton(entry.runtime_data)])


class SyncNowButton(MijnHostEntity, ButtonEntity):
    """Trigger an immediate check-and-sync."""

    _attr_translation_key = "sync_now"
    _attr_icon = "mdi:refresh"
    suffix = "sync_now"

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()
