"""Config flow for CBR Currency integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.config_entries import ConfigEntry, OptionsFlow

from .const import (
    CONF_CURRENCIES,
    CONF_SCAN_INTERVAL,
    CURRENCY_OPTIONS,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    SCAN_INTERVAL_OPTIONS,
)

_LOGGER = logging.getLogger(__name__)

class CBRCurrencyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CBR Currency."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            return self.async_create_entry(
                title=DEFAULT_NAME,
                data={},
                options={
                    CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                    CONF_CURRENCIES: user_input[CONF_CURRENCIES],
                },
            )

        schema = vol.Schema({
            vol.Required(
                CONF_CURRENCIES,
                default=["USD", "EUR"],
            ): cv.multi_select({k: v for k, v in CURRENCY_OPTIONS}),
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=str(DEFAULT_SCAN_INTERVAL),
            ): vol.In({str(k): v for k, v in SCAN_INTERVAL_OPTIONS}),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> CBRCurrencyOptionsFlow:
        """Get the options flow for this handler."""
        return CBRCurrencyOptionsFlow(config_entry)

class CBRCurrencyOptionsFlow(OptionsFlow):
    """Handle options flow for CBR Currency."""
    
    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        # Don't set self.config_entry explicitly - it's handled by the parent class now
        pass

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors = {}

        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                    CONF_CURRENCIES: user_input[CONF_CURRENCIES],
                },
            )

        current_currencies = self.config_entry.options.get(CONF_CURRENCIES, ["USD", "EUR"])
        current_interval = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        schema = vol.Schema({
            vol.Required(
                CONF_CURRENCIES,
                default=current_currencies,
            ): cv.multi_select({k: v for k, v in CURRENCY_OPTIONS}),
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=current_interval,
            ): vol.In({str(k): v for k, v in SCAN_INTERVAL_OPTIONS}),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
