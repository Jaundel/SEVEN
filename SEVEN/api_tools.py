# ============================================================
#  File: api_tools.py
#  Project: SEVEN (Sustainable Energy via Efficient Neural-routing)
#  Description: Integrations with real-time APIs (weather, crypto, news).
#  Author(s): Team SEVEN
#  Date: 2025-11-16
# ============================================================
"""Helpers for fetching concise real-time data snippets."""

from __future__ import annotations

import logging
import os
import re
from typing import Optional
from urllib.parse import quote_plus

import requests

LOGGER = logging.getLogger(__name__)

OPENWEATHER_ENDPOINT = "https://api.openweathermap.org/data/2.5/weather"
NEWS_ENDPOINT = "https://newsapi.org/v2/everything"
COINDESK_ENDPOINT = "https://production.api.coindesk.com/v2/tb/price/ticker"

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _extract_location(prompt: str) -> Optional[str]:
    """Extract a simple '<preposition> <location>' phrase from the prompt."""
    if not prompt:
        return None
    match = re.search(r"\b(?:in|at)\s+([A-Za-z\s,]+)", prompt, re.IGNORECASE)
    if not match:
        return None
    location = match.group(1).split("?")[0].strip(" .,!?")
    return location or None


def _resolve_topic(prompt: str) -> str:
    """Return a topic string safe for use with NewsAPI."""
    if prompt and prompt.strip():
        return prompt.strip()
    return "technology"


# ---------------------------------------------------------------------------
# Weather (OpenWeather)
# ---------------------------------------------------------------------------

def get_weather(prompt: str) -> str:
    """Return a short weather summary using OpenWeather data."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "Weather data unavailable (set OPENWEATHER_API_KEY)."

    location = _extract_location(prompt) or "New York"
    params = {"q": location, "appid": api_key, "units": "metric"}

    try:
        response = requests.get(OPENWEATHER_ENDPOINT, params=params, timeout=6)
        response.raise_for_status()
        payload = response.json()

        if str(payload.get("cod")) != "200":
            message = payload.get("message", "unknown error")
            raise RuntimeError(message)

        main = payload.get("main", {})
        weather_desc = (
            payload.get("weather", [{}])[0].get("description", "n/a").capitalize()
        )
        temp_c = main.get("temp")
        humidity = main.get("humidity")
        name = payload.get("name") or location

        parts = [f"{name}: {weather_desc}"]
        if temp_c is not None:
            parts.append(f"{temp_c:.1f} deg C")
        if humidity is not None:
            parts.append(f"humidity {humidity}%")
        return ", ".join(parts) + " (OpenWeather)"
    except Exception as exc:
        LOGGER.warning("OpenWeather lookup failed: %s", exc)
        return f"Weather data unavailable ({exc})"


# ---------------------------------------------------------------------------
# Crypto (CoinDesk)
# ---------------------------------------------------------------------------

COIN_ALIASES = {
    "bitcoin": "BTC",
    "btc": "BTC",
    "satoshi": "BTC",
    "ethereum": "ETH",
    "eth": "ETH",
    "solana": "SOL",
    "sol": "SOL",
    "dogecoin": "DOGE",
    "doge": "DOGE",
}


def _resolve_coin_symbol(prompt: str) -> str:
    lowered = (prompt or "").lower()
    for alias, symbol in COIN_ALIASES.items():
        if alias in lowered:
            return symbol
    return "BTC"


def get_crypto_price(prompt: str) -> str:
    """Return a USD spot price for a requested asset via CoinDesk."""
    api_key = os.getenv("COINDESK_API_KEY")
    if not api_key:
        return "Crypto data unavailable (set COINDESK_API_KEY)."

    symbol = _resolve_coin_symbol(prompt)
    headers = {"X-CoinDesk-API-Key": api_key}
    params = {"assets": symbol}

    try:
        response = requests.get(
            COINDESK_ENDPOINT, headers=headers, params=params, timeout=6
        )
        response.raise_for_status()
        payload = response.json()
        asset_data = (
            payload.get("data", {}).get(symbol.lower())
            or payload.get("data", {}).get(symbol.upper())
            or payload.get("data", {}).get(symbol)
        )
        if asset_data is None:
            raise RuntimeError("Asset not found in CoinDesk response.")

        price = (
            asset_data.get("price")
            or (asset_data.get("ohlc") or {}).get("c")
            or (asset_data.get("ohlc") or {}).get("close")
            or (asset_data.get("spot") or {}).get("price")
            or (asset_data.get("quote") or {}).get("USD", {}).get("price")
            or (asset_data.get("quote") or {}).get("usd", {}).get("price")
        )
        if price is None:
            raise RuntimeError("Price missing from CoinDesk response.")

        return f"{symbol}: ${price:,.2f} USD (CoinDesk)"
    except Exception as exc:
        LOGGER.warning("CoinDesk lookup failed: %s", exc)
        return f"Crypto price unavailable ({exc})"


# ---------------------------------------------------------------------------
# News (NewsAPI.org)
# ---------------------------------------------------------------------------

def get_news(prompt: str) -> str:
    """Return the freshest headline for the given topic using NewsAPI."""
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return "News data unavailable (set NEWS_API_KEY)."

    topic = _resolve_topic(prompt)
    params = {
        "q": topic,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": 1,
        "apiKey": api_key,
    }

    try:
        response = requests.get(NEWS_ENDPOINT, params=params, timeout=6)
        response.raise_for_status()
        payload = response.json()
        articles = payload.get("articles") or []
        if not articles:
            return f"No recent headlines for '{topic}'."
        article = articles[0]
        title = article.get("title") or "Untitled story"
        source = (article.get("source") or {}).get("name") or "Unknown source"
        url = article.get("url") or ""
        return f"{title} - {source} ({url})"
    except Exception as exc:
        LOGGER.warning("NewsAPI lookup failed: %s", exc)
        return f"News data unavailable ({exc})"


__all__ = ["get_weather", "get_crypto_price", "get_news"]
