"""Sensor for CBR currency rates."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from typing import Any
import urllib.request

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import Throttle

from .const import (
    ATTRIBUTION,
    BASE_URL,
    CURRENCY_CODES,
    CONF_CURRENCIES,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the CBR currency sensors from a config entry."""
    options = config_entry.options
    
    scan_interval = timedelta(minutes=int(options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)))
    currencies = options.get(CONF_CURRENCIES, ["USD", "EUR"])

    entities = []
    for currency in currencies:
        if currency in CURRENCY_CODES:
            sensor = CBRCurrencySensor(
                currency,
                scan_interval,
                hass,
            )
            entities.append(sensor)
    
    async_add_entities(entities, True)

class CBRCurrencySensor(SensorEntity):
    """Representation of a CBR currency sensor."""

    _attr_has_entity_name = True
    _attr_translation_key = "cbr_exchange_rates"

    def __init__(self, currency: str, scan_interval: timedelta, hass: HomeAssistant) -> None:
        """Initialize the sensor."""
        self._currency = currency
        self._hass = hass
        self._attr_name = f"CBR {currency} Exchange Rate"
        self._attr_icon = "mdi:currency-usd" if currency == "USD" else "mdi:currency-eur"
        self._attr_native_unit_of_measurement = "RUB"
        self._attr_attribution = ATTRIBUTION
        self._attr_unique_id = f"cbr_{currency.lower()}_exchange_rate"
        self._attr_extra_state_attributes = {
            "currency": currency,
            "rate_previous": None,
            "change": None,
            "change_amount": None,
            "date": None,
            "date_previous": None,
        }
        
        # Set up throttling
        self.update = Throttle(scan_interval)(self._update)
        
        # Schedule initial update
        hass.async_create_task(self.async_update())

    async def async_update(self) -> None:
        """Update the sensor data."""
        await self._hass.async_add_executor_job(self._update)

    def _update(self) -> None:
        """Get the latest data and updates the states."""
        _LOGGER.debug(f"Updating CBR currency data for {self._currency}")
        try:
            # Get current rates using urllib (synchronous)
            with urllib.request.urlopen(BASE_URL, timeout=10) as response:
                xml_data = response.read()
                current_root = ET.fromstring(xml_data)
                current_date = current_root.attrib['Date']
                
                # Get previous day rates
                prev_date = (datetime.strptime(current_date, "%d.%m.%Y") - timedelta(days=1)).strftime("%d.%m.%Y")
                prev_url = f"{BASE_URL}?date_req={prev_date}"
                with urllib.request.urlopen(prev_url, timeout=10) as prev_response:
                    prev_xml = prev_response.read()
                    prev_root = ET.fromstring(prev_xml)
            
            # Parse values
            current_rate = self._parse_rate(current_root)
            previous_rate = self._parse_rate(prev_root)
            
            # Calculate changes
            change_amount = current_rate - previous_rate
            change = "up" if change_amount > 0 else "down" if change_amount < 0 else "same"
            change_amount = abs(change_amount)
            
            # Update attributes
            self._attr_native_value = current_rate
            self._attr_extra_state_attributes.update({
                "rate_previous": previous_rate,
                "change": change,
                "change_amount": change_amount,
                "date": current_date,
                "date_previous": prev_date,
                "rate_formatted": self._format_currency(current_rate),
                "change_formatted": self._format_currency(change_amount),
            })
            
            _LOGGER.debug(f"Successfully updated CBR currency data for {self._currency}")
            
        except Exception as ex:
            _LOGGER.error(f"Error updating CBR currency data: {str(ex)}")
            self._attr_native_value = None
            self._attr_extra_state_attributes.update({
                "error": str(ex),
                "rate_previous": None,
                "change": None,
                "change_amount": None,
                "date": None,
                "date_previous": None,
            })

    def _parse_rate(self, root: ET.Element) -> float:
        """Parse the currency rate from the XML."""
        for valute in root.findall('Valute'):
            if valute.find('CharCode').text == self._currency:
                value = valute.find('Value').text.replace(",", ".")
                return round(float(value), 4)
        return 0.0

    def _format_currency(self, num: float | None) -> str:
        """Format currency value as string with rubles and kopecks."""
        if num is None or num <= 0:
            return "0 рублей ровно"
        
        rur = int(num)
        penny = int(round((num - rur) * 100, 0))
        
        if penny >= 100:
            penny = 0
            rur += 1
        
        if penny == 0:
            return f"{rur} {self._rub(rur)} ровно"
        return f"{rur} {self._rub(rur)} {penny} {self._kop(penny)}"

    def _rub(self, num: int) -> str:
        """Return correct russian word for rubles."""
        reminder = num % 100 if num >= 100 else num % 10
        if num == 0 or reminder == 0 or reminder >= 5 or num in range(11, 19):
            return "рублей"
        elif reminder == 1:
            return "рубль"
        return "рубля"

    def _kop(self, num: int) -> str:
        """Return correct russian word for kopecks."""
        reminder = num % 10
        if num <= 0:
            return "ровно"
        elif reminder == 0 or reminder >= 5 or num in range(11, 19):
            return "копеек"
        elif reminder == 1:
            return "копейка"
        return "копейки"