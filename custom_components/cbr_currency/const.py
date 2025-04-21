"""Constants for CBR Currency integration."""
from datetime import timedelta

DOMAIN = "cbr_currency"
ATTRIBUTION = "Данные предоставлены Центральным Банком России"

DEFAULT_NAME = "CBR Exchange rates"
# DEFAULT_SCAN_INTERVAL = timedelta(minutes=5)
DEFAULT_SCAN_INTERVAL = 5

CONF_SCAN_INTERVAL = "scan_interval"
CONF_CURRENCIES = "currencies"

CURRENCY_CODES = {
    "USD": "R01235",
    "EUR": "R01239"
}

BASE_URL = "https://www.cbr.ru/scripts/XML_daily.asp"

CURRENCY_OPTIONS = [
    ("USD", "Доллар США (USD)"),
    ("EUR", "Евро (EUR)"),
]

SCAN_INTERVAL_OPTIONS = [
    (1, "1 минута"),
    (5, "5 минут"),
    (15, "15 минут"),
    (30, "30 минут"),
    (60, "1 час"),
    (180, "3 часа"),
    (360, "6 часов"),
    (720, "12 часов"),
    (1440, "1 день"),
]