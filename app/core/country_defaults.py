from typing import TypedDict


class CountryDefaults(TypedDict):
    timezone: str
    currency_code: str
    country_code: str
    phone_country_code: str
    language_code: str  # ISO 639-1 tag, e.g. "he", "en-GB", "en-AU"
    date_format: str    # strftime format for PDF documents
    text_direction: str # "rtl" or "ltr" for PDF/HTML rendering


COUNTRY_DEFAULTS: dict[str, CountryDefaults] = {
    "Israel": {
        "timezone": "Asia/Jerusalem",
        "currency_code": "ILS",
        "country_code": "IL",
        "phone_country_code": "+972",
        "language_code": "he",
        "date_format": "%d/%m/%Y",
        "text_direction": "rtl",
    },
    "United Kingdom": {
        "timezone": "Europe/London",
        "currency_code": "GBP",
        "country_code": "GB",
        "phone_country_code": "+44",
        "language_code": "en-GB",
        "date_format": "%d/%m/%Y",
        "text_direction": "ltr",
    },
    "Australia": {
        "timezone": "Australia/Sydney",
        "currency_code": "AUD",
        "country_code": "AU",
        "phone_country_code": "+61",
        "language_code": "en-AU",
        "date_format": "%d/%m/%Y",
        "text_direction": "ltr",
    },
    "United States": {
        "timezone": "America/New_York",
        "currency_code": "USD",
        "country_code": "US",
        "phone_country_code": "+1",
        "language_code": "en-US",
        "date_format": "%m/%d/%Y",
        "text_direction": "ltr",
    },
    "Germany": {
        "timezone": "Europe/Berlin",
        "currency_code": "EUR",
        "country_code": "DE",
        "phone_country_code": "+49",
        "language_code": "de",
        "date_format": "%d.%m.%Y",
        "text_direction": "ltr",
    },
    "France": {
        "timezone": "Europe/Paris",
        "currency_code": "EUR",
        "country_code": "FR",
        "phone_country_code": "+33",
        "language_code": "fr",
        "date_format": "%d/%m/%Y",
        "text_direction": "ltr",
    },
}


def get_country_defaults(country: str) -> CountryDefaults:
    """Returns defaults for the given country, or raises ValueError if not supported."""
    defaults = COUNTRY_DEFAULTS.get(country)
    if not defaults:
        supported = ", ".join(COUNTRY_DEFAULTS.keys())
        raise ValueError(
            f"Country '{country}' not supported yet. Supported: {supported}"
        )
    return defaults
