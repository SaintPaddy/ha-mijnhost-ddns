"""Base entity for mijn.host DDNS."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MijnHostCoordinator


class MijnHostEntity(CoordinatorEntity[MijnHostCoordinator]):
    """Common base: one service device per managed record."""

    _attr_has_entity_name = True
    suffix: str

    def __init__(self, coordinator: MijnHostCoordinator) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{self.suffix}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"mijn.host DDNS {coordinator.record_name}",
            manufacturer="mijn.host",
            model="Dynamic DNS updater",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://mijn.host/cp/",
        )
