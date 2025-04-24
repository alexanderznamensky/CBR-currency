"""Config flow for CBR Currency integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.config_entries import ConfigEntry, OptionsFlow
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry

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
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

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
            ): cv.multi_select(CURRENCY_OPTIONS),
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=DEFAULT_SCAN_INTERVAL,
            ): vol.In(SCAN_INTERVAL_OPTIONS),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.entry = entry
        self.current_currencies = set(entry.options.get(CONF_CURRENCIES, ["USD", "EUR"]))

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            new_currencies = set(user_input[CONF_CURRENCIES])
            
            # Определяем валюты для удаления
            currencies_to_remove = self.current_currencies - new_currencies
            
            # Сохраняем новые настройки
            new_data = {**self.entry.options, **user_input}
            
            # Обновляем конфигурацию
            self.hass.config_entries.async_update_entry(
                self.entry,
                options=new_data
            )
            
            # Удаляем сенсоры для убранных валют
            if currencies_to_remove:
                await self._remove_unused_sensors(currencies_to_remove)
            
            # Перезагружаем интеграцию для применения изменений
            await self.hass.config_entries.async_reload(self.entry.entry_id)
            
            return self.async_create_entry(title="", data=new_data)


        schema = vol.Schema({
            vol.Required(
                CONF_CURRENCIES,
                default=self.entry.options.get(CONF_CURRENCIES, ["USD", "EUR"]),
            ): cv.multi_select(CURRENCY_OPTIONS),
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=self.entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): vol.In(SCAN_INTERVAL_OPTIONS),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )


    async def _remove_unused_sensors(self, currencies_to_remove: set[str]) -> None:
        """Remove sensors for currencies that were removed from config."""
        registry = entity_registry.async_get(self.hass)
        for currency in currencies_to_remove:
            entity_id = registry.async_get_entity_id(
                "sensor",
                DOMAIN,
                f"cbr_{currency.lower()}_exchange_rate"
            )
            if entity_id:
                registry.async_remove(entity_id)