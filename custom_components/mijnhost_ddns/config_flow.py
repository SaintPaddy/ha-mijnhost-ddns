"""Config flow for mijn.host DDNS."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_API_KEY
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import MijnHostAuthError, MijnHostClient, MijnHostError
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

API_KEY_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DNS_DOMAIN): TextSelector(),
        vol.Required(CONF_RECORD_NAME): TextSelector(),
        vol.Required(CONF_API_KEY): API_KEY_SELECTOR,
    }
)


def _ip_source_selector() -> SelectSelector:
    options = [
        SelectOptionDict(value=key, label=label)
        for key, (label, _url) in IP_SOURCES.items()
    ]
    options.append(
        SelectOptionDict(value=IP_SOURCE_CUSTOM, label="Custom URL (plain-text IPv4 echo)")
    )
    return SelectSelector(
        SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN)
    )


class MijnHostConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial and reauth flows."""

    VERSION = 1

    async def _async_validate(self, dns_domain: str, api_key: str) -> str | None:
        """Return an error key, or None when the credentials work."""
        client = MijnHostClient(async_get_clientsession(self.hass), api_key)
        try:
            await client.get_records(dns_domain)
        except MijnHostAuthError:
            return "invalid_auth"
        except MijnHostError:
            return "cannot_connect"
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Unexpected error validating mijn.host access")
            return "unknown"
        return None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            dns_domain = user_input[CONF_DNS_DOMAIN].strip().strip(".").lower()
            record_name = user_input[CONF_RECORD_NAME].strip().strip(".").lower()
            if not record_name.endswith(dns_domain):
                record_name = f"{record_name}.{dns_domain}"
            error = await self._async_validate(dns_domain, user_input[CONF_API_KEY])
            if error is None:
                await self.async_set_unique_id(f"{dns_domain}:{record_name}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=record_name,
                    data={
                        CONF_DNS_DOMAIN: dns_domain,
                        CONF_RECORD_NAME: record_name,
                        CONF_API_KEY: user_input[CONF_API_KEY],
                    },
                    options={
                        CONF_IP_SOURCE: DEFAULT_IP_SOURCE,
                        CONF_TTL: DEFAULT_TTL,
                        CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL_MINUTES,
                    },
                )
            errors["base"] = error
        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """API key was rejected at runtime; ask for a new one."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()
        if user_input is not None:
            error = await self._async_validate(
                reauth_entry.data[CONF_DNS_DOMAIN], user_input[CONF_API_KEY]
            )
            if error is None:
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data_updates={CONF_API_KEY: user_input[CONF_API_KEY]},
                )
            errors["base"] = error
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): API_KEY_SELECTOR}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> MijnHostOptionsFlow:
        return MijnHostOptionsFlow()


class MijnHostOptionsFlow(OptionsFlow):
    """Options: IP lookup source, TTL, check interval."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        options = self.config_entry.options
        if user_input is not None:
            custom_url = str(user_input.get(CONF_CUSTOM_IP_URL, "")).strip()
            if user_input.get(
                CONF_IP_SOURCE
            ) == IP_SOURCE_CUSTOM and not custom_url.startswith("https://"):
                errors["base"] = "custom_url_required"
            else:
                return self.async_create_entry(title="", data=user_input)
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_IP_SOURCE,
                    default=options.get(CONF_IP_SOURCE, DEFAULT_IP_SOURCE),
                ): _ip_source_selector(),
                vol.Optional(
                    CONF_CUSTOM_IP_URL,
                    default=options.get(CONF_CUSTOM_IP_URL, ""),
                ): TextSelector(TextSelectorConfig(type=TextSelectorType.URL)),
                vol.Required(
                    CONF_TTL, default=options.get(CONF_TTL, DEFAULT_TTL)
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=60,
                        max=86400,
                        step=60,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="s",
                    )
                ),
                vol.Required(
                    CONF_UPDATE_INTERVAL,
                    default=options.get(
                        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_MINUTES
                    ),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1,
                        max=1440,
                        step=1,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="min",
                    )
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
