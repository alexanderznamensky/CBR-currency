"""Sensor for CBR currency rates."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from typing import Any
from urllib.request import urlopen
import socket

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.storage import Store

from .const import (
    ATTRIBUTION,
    BASE_URL,
    CONF_CURRENCIES,
    CURRENCY_OPTIONS,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    CURRENCY_OPTIONS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STORAGE_KEY = "cbr_currency_rate_storage"
STORAGE_VERSION = 1

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the CBR currency sensors from a config entry."""
    config = config_entry.options
    scan_interval = timedelta(seconds=config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL * 60))
    currencies = config.get(CONF_CURRENCIES, ["USD", "EUR"])

    coordinator = CBRCurrencyCoordinator(hass, scan_interval)
    
    # Загружаем предыдущее состояние timestamp и даты курса
    await coordinator.async_load_last_state()

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    entities = []
    for currency in currencies:
        if currency in CURRENCY_OPTIONS:
            entities.append(CBRCurrencySensor(coordinator, currency, scan_interval))
    
    async_add_entities(entities)

class CBRCurrencyCoordinator(DataUpdateCoordinator):
    """Class to manage fetching CBR currency data."""
    
    def __init__(self, hass: HomeAssistant, update_interval: timedelta):
        """Initialize global CBR currency data updater."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.previous_rates = None
        self.previous_date = None
        self.new_rate_timestamp = None
        self.last_known_course_date = None

    async def async_load_last_state(self):
        """Load last known course date and timestamp from storage."""
        data = await self._store.async_load()
        if data:
            self.last_known_course_date = data.get("last_known_course_date")
            self.new_rate_timestamp = data.get("new_rate_timestamp")
            _LOGGER.debug("Loaded last state from storage: %s", data)

    async def async_save_state(self):
        """Save current course date and timestamp to storage."""
        await self._store.async_save({
            "last_known_course_date": self.last_known_course_date,
            "new_rate_timestamp": self.new_rate_timestamp,
        })
        _LOGGER.debug(
            "Saved state to storage: last_known_course_date=%s, new_rate_timestamp=%s",
            self.last_known_course_date,
            self.new_rate_timestamp,
        )

    async def _async_update_data(self):
        """Fetch data from CBR API."""
        try:
            current_data = await self.hass.async_add_executor_job(self._fetch_cbr_data)
            current_course_date = current_data['date']  # дата курса из XML

            # === Запоминание момента появления нового курса ===
            if self.last_known_course_date != current_course_date:
                self.new_rate_timestamp = datetime.now().isoformat()
                self.last_known_course_date = current_course_date
                # Сохраняем новое состояние
                await self.async_save_state()

            # Передаём этот timestamp дальше
            current_data['new_rate_timestamp'] = self.new_rate_timestamp

            # Получаем данные за предыдущий день
            try:
                prev_date = (datetime.strptime(current_data['date'], "%d.%m.%Y") - timedelta(days=1)).strftime("%d.%m.%Y")
                prev_url = f"{BASE_URL}?date_req={prev_date}"
                self.previous_rates = await self.hass.async_add_executor_job(self._fetch_cbr_data, prev_url)
                self.previous_date = prev_date
            except Exception as prev_err:
                _LOGGER.warning(f"Could not fetch previous day rates: {prev_err}")
                self.previous_rates = None
                self.previous_date = None

            return current_data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with CBR API: {err}")

    def _fetch_cbr_data(self, url: str = BASE_URL):
        """Fetch data from CBR website."""
        try:
            socket.setdefaulttimeout(10)
            with urlopen(url) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                
                rates = {}
                for valute in root.findall('Valute'):
                    char_code = valute.find('CharCode').text
                    if char_code in CURRENCY_OPTIONS:
                        value = float(valute.find('Value').text.replace(",", "."))
                        nominal = int(valute.find('Nominal').text)
                        rates[char_code] = round(value / nominal, 4) 
                
                return {
                    'rates': rates,
                    'date': root.attrib['Date'],
                    'timestamp': datetime.now().isoformat(),
                    'current_date': datetime.now().strftime("%d.%m.%Y"), 
                }
        except Exception as err:
            raise UpdateFailed(f"Error fetching CBR data from {url}: {err}")

class CBRCurrencySensor(SensorEntity):
    """Representation of a CBR currency sensor."""

    _attr_attribution = ATTRIBUTION
    _attr_native_unit_of_measurement = "RUB"
    _attr_translation_key = "cbr_exchange_rates"
    _attr_state_class = "measurement"
    _attr_should_poll = False

    def __init__(self, coordinator: CBRCurrencyCoordinator, currency: str, scan_interval: timedelta):
        """Initialize the sensor."""
        self._coordinator = coordinator
        self._currency = currency
        self._scan_interval_minutes = scan_interval.total_seconds() / 60 
        self._attr_name = f"CBR {currency} Exchange Rate"
        self._attr_unique_id = f"cbr_{currency.lower()}_exchange_rate"
        # Устанавливаем иконку с fallback на mdi:currency-usd-off
        icon_name = f"mdi:currency-{currency.lower()}"
        try:
            # Проверяем существование иконки
            if not self._icon_exists(icon_name):
                raise ValueError("Icon not found")
            self._attr_icon = icon_name
        except:
            self._attr_icon = "mdi:currency-usd-off"

    def _icon_exists(self, icon_name: str) -> bool:
        """Check if icon exists in MDI."""
        known_icons = ["usd", "eur", "gbp", "jpy", "cny", "rub"]
        return any(icon_name.endswith(x) for x in known_icons)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._coordinator.last_update_success and self._currency in self._coordinator.data.get('rates', {})

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        rate = self._coordinator.data.get('rates', {}).get(self._currency)
        return round(rate, 4) if rate is not None else None 

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.available:
            return {} 

        current_rate = self.native_value
        current_date = self._coordinator.data.get('date')
        previous_rate = self._coordinator.previous_rates.get('rates', {}).get(self._currency) if self._coordinator.previous_rates else None
        previous_date = self._coordinator.previous_date
        
        # Calculate changes
        change = None
        change_amount = None
        if current_rate is not None and previous_rate is not None:
            change_amount = round(current_rate - previous_rate, 4) 
            if change_amount > 0:
                change = "up"
            elif change_amount < 0:
                change = "down"
            else:
                change = "same"
            change_amount = abs(change_amount)
        
        attributes = {
            "currency": self._currency,
            "currency_name": CURRENCY_OPTIONS.get(self._currency, self._currency),
            "rate": current_rate,
            "rate_previous": previous_rate,
            "rate_formatted": self._format_currency(current_rate),
            "previous_rate_formatted": self._format_currency(previous_rate),
            "current_date": self._coordinator.data.get('current_date'),
            "date": current_date,
            "date_previous": previous_date,
            "update_interval_minutes": round(self._scan_interval_minutes, 2), 
            "change": change,
            "change_amount": change_amount,
            "change_formatted": self._format_currency(change_amount) if change_amount is not None else None,
            "last_updated": self._coordinator.data.get('timestamp'),
            "new_rate_timestamp": self._coordinator.data.get('new_rate_timestamp'),
        }
        
        return {k: v for k, v in attributes.items() if v is not None}

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self._coordinator.async_add_listener(
                self.async_write_ha_state
            )
        )

    def _format_currency(self, num: float | None) -> str:
        """Format currency value as string with rubles and kopecks."""
        if num is None or num <= 0:
            return "0 рублей ровно"
        
        rubles = int(num)
        kopecks = int(round((num - rubles) * 100, 0))
        
        if kopecks >= 100:
            kopecks = 0
            rubles += 1
        
        if kopecks == 0:
            return f"{rubles} {self._rub(rubles)} ровно"
        return f"{rubles} {self._rub(rubles)} {kopecks} {self._kop(kopecks)}"

    def _rub(self, num: int) -> str:
        """Return correct russian word for rubles."""
        if num % 100 in range(11, 20):
            return "рублей"
        last_digit = num % 10
        if last_digit == 1:
            return "рубль"
        if last_digit in (2, 3, 4):
            return "рубля"
        return "рублей"

    def _kop(self, num: int) -> str:
        """Return correct russian word for kopecks."""
        if num % 100 in range(11, 20):
            return "копеек"
        last_digit = num % 10
        if last_digit == 1:
            return "копейку"
        if last_digit in (2, 3, 4):
            return "копейки"
        return "копеек"
