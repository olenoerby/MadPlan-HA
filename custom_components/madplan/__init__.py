"""The MadPlan integration: meal plan, shopping list, budget and pantry in Home Assistant."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN, CONF_URL, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol

from .api import MadPlanClient, MadPlanError
from .const import (
    DOMAIN,
    SERVICE_ADD_TO_SHOPPING_LIST,
    SERVICE_MEAL_COOKED,
    SERVICE_SEND_TO_MEALIE,
    SERVICE_UPDATE_PANTRY,
    SERVICE_VOTE_MEAL,
)
from .coordinator import MadPlanCoordinator

PLATFORMS = [Platform.CALENDAR, Platform.SENSOR, Platform.TODO]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type MadPlanConfigEntry = ConfigEntry[MadPlanCoordinator]

_ADD_SCHEMA = vol.Schema({vol.Required("name"): cv.string})
_PANTRY_SCHEMA = vol.Schema(
    {
        vol.Required("name"): cv.string,
        vol.Optional("quantity"): vol.Coerce(float),
        vol.Optional("unit"): cv.string,
        vol.Optional("expires_on"): cv.date,
        vol.Optional("min_quantity"): vol.Coerce(float),
    }
)
_VOTE_SCHEMA = vol.Schema({vol.Required("meal_id"): vol.Coerce(int), vol.Required("vote"): vol.In(["yes", "no"])})
_COOKED_SCHEMA = vol.Schema({vol.Required("meal_id"): vol.Coerce(int), vol.Required("cooked"): cv.boolean})


def _first_client(hass: HomeAssistant) -> MadPlanCoordinator:
    for entry in hass.config_entries.async_loaded_entries(DOMAIN):
        return entry.runtime_data
    raise HomeAssistantError("MadPlan is not set up")


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Registers the services, so that they exist even while the server is unreachable."""

    async def add_to_shopping_list(call: ServiceCall) -> None:
        coordinator = _first_client(hass)
        try:
            await coordinator.client.add_item(call.data["name"])
        except MadPlanError as exc:
            raise HomeAssistantError(str(exc)) from exc
        await coordinator.async_request_refresh()

    async def update_pantry(call: ServiceCall) -> None:
        coordinator = _first_client(hass)
        payload = dict(call.data)
        if "expires_on" in payload:
            payload["expires_on"] = payload["expires_on"].isoformat()
        try:
            await coordinator.client.update_pantry(payload)
        except MadPlanError as exc:
            raise HomeAssistantError(str(exc)) from exc
        await coordinator.async_request_refresh()

    async def vote_meal(call: ServiceCall) -> None:
        coordinator = _first_client(hass)
        try:
            await coordinator.client.vote_meal(call.data["meal_id"], call.data["vote"])
        except MadPlanError as exc:
            raise HomeAssistantError(str(exc)) from exc
        await coordinator.async_request_refresh()

    async def meal_cooked(call: ServiceCall) -> None:
        coordinator = _first_client(hass)
        try:
            await coordinator.client.meal_cooked(call.data["meal_id"], call.data["cooked"])
        except MadPlanError as exc:
            raise HomeAssistantError(str(exc)) from exc
        await coordinator.async_request_refresh()

    async def send_to_mealie(call: ServiceCall) -> None:
        """The plan page's send button, pressed from a phone. A person still decides when."""
        coordinator = _first_client(hass)
        try:
            await coordinator.client.send_to_mealie()
        except MadPlanError as exc:
            raise HomeAssistantError(str(exc)) from exc
        await coordinator.async_request_refresh()

    hass.services.async_register(DOMAIN, SERVICE_SEND_TO_MEALIE, send_to_mealie)
    hass.services.async_register(DOMAIN, SERVICE_ADD_TO_SHOPPING_LIST, add_to_shopping_list, schema=_ADD_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_VOTE_MEAL, vote_meal, schema=_VOTE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_MEAL_COOKED, meal_cooked, schema=_COOKED_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_UPDATE_PANTRY, update_pantry, schema=_PANTRY_SCHEMA)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: MadPlanConfigEntry) -> bool:
    client = MadPlanClient(async_get_clientsession(hass), entry.data[CONF_URL], entry.data[CONF_TOKEN])
    coordinator = MadPlanCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_reload_on_change))
    return True


async def _reload_on_change(hass: HomeAssistant, entry: MadPlanConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: MadPlanConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
