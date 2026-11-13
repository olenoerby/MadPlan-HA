"""What all MadPlan entities have in common."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MadPlanCoordinator


class MadPlanEntity(CoordinatorEntity[MadPlanCoordinator]):
    _attr_has_entity_name = True
    platform_domain: str

    def __init__(self, coordinator: MadPlanCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry_id = coordinator.config_entry.entry_id
        self._attr_unique_id = f"{entry_id}_{key}"
        # The same in every language and for every household's name, so that a dashboard or an
        # automation can be copied as it is. What is shown still follows the language.
        self.entity_id = f"{self.platform_domain}.madplan_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=coordinator.config_entry.title,
            manufacturer="MadPlan",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=coordinator.config_entry.data.get("url"),
        )
