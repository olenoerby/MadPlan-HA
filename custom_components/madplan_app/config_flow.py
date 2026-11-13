"""Setting MadPlan up from the Home Assistant UI."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_TOKEN, CONF_URL
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol

from .api import MadPlanAuthError, MadPlanClient, MadPlanError
from .const import CONF_SCAN_MINUTES, DEFAULT_SCAN_MINUTES, DOMAIN


class MadPlanConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _test(self, url: str, token: str) -> tuple[dict[str, Any] | None, str | None]:
        client = MadPlanClient(async_get_clientsession(self.hass), url, token)
        try:
            return await client.summary(), None
        except MadPlanAuthError:
            return None, "invalid_auth"
        except MadPlanError:
            return None, "cannot_connect"

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            url = user_input[CONF_URL].rstrip("/")
            summary, error = await self._test(url, user_input[CONF_TOKEN])
            if error:
                errors["base"] = error
            else:
                await self.async_set_unique_id(url)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=(summary or {}).get("household") or "MadPlan",
                    data={CONF_URL: url, CONF_TOKEN: user_input[CONF_TOKEN]},
                )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_URL): str, vol.Required(CONF_TOKEN): str}),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            _, error = await self._test(entry.data[CONF_URL], user_input[CONF_TOKEN])
            if error:
                errors["base"] = error
            else:
                return self.async_update_reload_and_abort(entry, data_updates={CONF_TOKEN: user_input[CONF_TOKEN]})
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return MadPlanOptionsFlow()


class MadPlanOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        current = self.config_entry.options.get(CONF_SCAN_MINUTES, DEFAULT_SCAN_MINUTES)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {vol.Required(CONF_SCAN_MINUTES, default=current): vol.All(vol.Coerce(int), vol.Range(min=1, max=1440))}
            ),
        )
