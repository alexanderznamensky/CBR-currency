"""Constants for CBR Currency integration."""
from datetime import timedelta

DOMAIN = "cbr_currency"
ATTRIBUTION = "Данные предоставлены Центральным Банком России"

DEFAULT_NAME = "CBR Exchange rates"
DEFAULT_SCAN_INTERVAL = 5*60
# DEFAULT_SCAN_INTERVAL = timedelta(minutes=5)

CONF_SCAN_INTERVAL = "scan_interval"
CONF_CURRENCIES = "currencies"

BASE_URL = "https://www.cbr.ru/scripts/XML_daily.asp"

CURRENCY_OPTIONS = {
    "AUD": "Австралийский доллар",
    "AZN": "Азербайджанский манат",
    "GBP": "Фунт стерлингов",
    "AMD": "Армянский драм",
    "BYN": "Белорусский рубль",
    "BGN": "Болгарский лев",
    "BRL": "Бразильский реал",
    "HUF": "Венгерский форинт",
    "HKD": "Гонконгский доллар",
    "DKK": "Датская крона",
    "USD": "Доллар США",
    "EUR": "Евро",
    "INR": "Индийская рупия",
    "KZT": "Казахстанский тенге",
    "CAD": "Канадский доллар",
    "KGS": "Киргизский сом",
    "CNY": "Китайский юань",
    "MDL": "Молдавский лей",
    "NOK": "Норвежская крона",
    "PLN": "Польский злотый",
    "RON": "Румынский лей",
    "XDR": "СДР (специальные права заимствования)",
    "SGD": "Сингапурский доллар",
    "TJS": "Таджикский сомони",
    "TRY": "Турецкая лира",
    "TMT": "Новый туркменский манат",
    "UZS": "Узбекский сум",
    "UAH": "Украинская гривна",
    "CZK": "Чешская крона",
    "SEK": "Шведская крона",
    "CHF": "Швейцарский франк",
    "ZAR": "Южноафриканский рэнд",
    "KRW": "Вон Республики Корея",
    "JPY": "Японская иена",
    "RSD": "Сербский динар",
    "NZD": "Новозеландский доллар",
    "GEL": "Грузинский Лари",
    "QAR": "Катарский риал",
    "EGP": "Египетский фунт",
    "AED": "Дирхам ОАЭ",
    "THB": "Таиландский бат",
    "IDR": "Индонезийская рупия",
    "VND": "Вьетнамский донг",
}

SCAN_INTERVAL_OPTIONS = {
    1*60: "1 минута",
    5*60: "5 минут",
    10*60: "10 минут",
    15*60: "15 минут",
    30*60: "30 минут",
    60*60: "1 час",
    180*60: "3 часа",
    360*60: "6 часов",
    720*60: "12 часов",
    1440*60: "1 день",
}
