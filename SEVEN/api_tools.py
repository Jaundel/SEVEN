# ============================================================
#  File: api_tools.py
#  Project: SEVEN (Sustainable Energy via Efficient Neural-routing)
#  Description: Helpers for fetching real-time weather/crypto/news data.
#  Author(s): Team SEVEN
#  Date: 2025-11-12
# ============================================================
"""Utility helpers that provide live data to the routing layer."""

from __future__ import annotations

import os
import re
from typing import Optional, Tuple

import requests

DEFAULT_WEATHER_CITY = os.getenv("DEFAULT_WEATHER_CITY", "Toronto")
NEWS_API_COUNTRY = os.getenv("NEWS_API_COUNTRY", "us")
COINGECKO_BASE_URL = os.getenv("COINGECKO_BASE_URL", "https://api.coingecko.com/api/v3")
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")

COINGECKO_IDS = {
    "btc": "bitcoin",
    "bitcoin": "bitcoin",
    "eth": "ethereum",
    "ethereum": "ethereum",
    "doge": "dogecoin",
    "dogecoin": "dogecoin",
}


def _request_timeout() -> float:
    raw = os.getenv("API_REQUEST_TIMEOUT_SECONDS")
    try:
        return float(raw) if raw else 5.0
    except ValueError:
        return 5.0


def _extract_city(prompt: str) -> Optional[str]:
    match = re.search(r"in ([A-Za-z\s]+)", prompt, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _detect_crypto(prompt: str) -> Tuple[str, str]:
    lowered = prompt.lower()
    for token, asset_id in COINGECKO_IDS.items():
        if token in lowered:
            return token.upper(), asset_id
    return "BTC", COINGECKO_IDS["btc"]


def get_weather(prompt: str) -> str:
    """Fetch current weather from OpenWeather."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "Missing OPENWEATHER_API_KEY environment variable."

    city = _extract_city(prompt) or DEFAULT_WEATHER_CITY
    params = {"q": city, "appid": api_key, "units": "metric"}
    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params=params,
            timeout=_request_timeout(),
        )
    except requests.RequestException as exc:
        return f"Weather API request failed: {exc}"

    if response.status_code != 200:
        return f"Weather API failed: {response.status_code}, {response.text}"

    data = response.json()
    try:
        temp_c = float(data["main"]["temp"])
        description = data["weather"][0]["description"]
    except (KeyError, TypeError, ValueError):
        return "Weather API returned an unexpected response."

    return f"The weather in {city} is {description} with {temp_c:.1f} deg C."


def get_crypto_price(prompt: str) -> str:
    """Fetch current crypto price using CoinGecko."""
    symbol, asset_id = _detect_crypto(prompt)
    headers = {}
    if COINGECKO_API_KEY:
        headers["x-cg-pro-api-key"] = COINGECKO_API_KEY

    params = {"ids": asset_id, "vs_currencies": "usd"}
    try:
        response = requests.get(
            f"{COINGECKO_BASE_URL.rstrip('/')}/simple/price",
            params=params,
            headers=headers,
            timeout=_request_timeout(),
        )
    except requests.RequestException as exc:
        return f"Crypto API request failed: {exc}"

    if response.status_code != 200:
        return f"Crypto API failed: {response.status_code}, {response.text}"

    data = response.json()
    price = data.get(asset_id, {}).get("usd")
    if price is None:
        return "Crypto API returned an unexpected response."

    return f"{symbol.upper()} is currently trading at ${price:,.2f} USD."


def get_news(prompt: str) -> str:
    """Fetch top headlines using NewsAPI."""
    del prompt  # Prompt not needed for generic top-headlines query.
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return "Missing NEWS_API_KEY environment variable."

    params = {"country": NEWS_API_COUNTRY, "pageSize": 3, "apiKey": api_key}
    try:
        response = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params=params,
            timeout=_request_timeout(),
        )
    except requests.RequestException as exc:
        return f"News API request failed: {exc}"

    if response.status_code != 200:
        return f"News API failed: {response.status_code}, {response.text}"

    data = response.json()
    articles = data.get("articles") or []
    headlines = [article.get("title", "Untitled") for article in articles[:3]]
    if not headlines:
        return "No headlines available right now."

    joined = "\n- ".join(headlines)
    return f"Here are the top headlines:\n- {joined}"


def detect_api_intent(prompt: str) -> Optional[str]:
    """Detect whether the prompt likely needs live data."""
    text = prompt.lower()
    if any(keyword in text for keyword in ["weather", "temperature", "forecast"]):
        return "weather"
    if any(keyword in text for keyword in ["bitcoin", "crypto", "ethereum", "dogecoin", "price"]):
        return "crypto"
    if any(keyword in text for keyword in ["news", "headline"]):
        return "news"
    return None
