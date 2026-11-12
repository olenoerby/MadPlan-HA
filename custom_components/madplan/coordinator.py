"""Polls MadPlan and shares the result between the entities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MadPlanAuthError, MadPlanClient, MadPlanError
from .const import CONF_SCAN_MINUTES, DEFAULT_SCAN_MINUTES, DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class MadPlanData:
    summary: dict[str, Any]
    meals: list[dict[str, Any]]
    shopping: dict[str, Any]


class MadPlanCoordinator(DataUpdateCoordinator[MadPlanData]):
    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: MadPlanClient) -> None:
        minutes = entry.options.get(CONF_SCAN_MINUTES, DEFAULT_SCAN_MINUTES)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=minutes),
        )
        self.client = client

    async def _async_update_data(self) -> MadPlanData:
        try:
            return MadPlanData(
                summary=await self.client.summary(),
                meals=await self.client.calendar(),
                shopping=await self.client.shopping(),
            )
        except MadPlanAuthError as exc:
            raise ConfigEntryAuthFailed(str(exc)) from exc
        except MadPlanError as exc:
            raise UpdateFailed(str(exc)) from exc
