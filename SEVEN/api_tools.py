# # ============================================================
# #  File: api_tools.py
# #  Project: SEVEN
# #  Description: Utility functions for fetching live data (weather, news, etc.)
# # ============================================================
# import os
# import re
# import requests
# from dotenv import load_dotenv

# load_dotenv()

# def detect_external_intent(prompt: str) -> str:
#     """
#     Detect if the user query requires internet-based info.
#     Returns 'weather', 'news', or 'none'.
#     """
#     text = prompt.lower()
#     if any(k in text for k in ["weather", "temperature", "forecast"]):
#         return "weather"
#     if any(k in text for k in ["news", "headline", "latest"]):
#         return "news"
#     return "none"


# def get_weather(prompt: str) -> str:
#     """
#     Fetch current weather from OpenWeather API.
#     """
#     api_key = os.getenv("OPENWEATHER_API_KEY")
#     if not api_key:
#         return "Weather API key not set in .env."

#     city_match = re.search(r"in ([A-Za-z\s]+)", prompt)
#     city = city_match.group(1).strip() if city_match else "Toronto"

#     url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
#     res = requests.get(url)
#     data = res.json()

#     if res.status_code != 200 or "main" not in data:
#         return f"Sorry, I couldn’t fetch the weather for {city}."

#     temp = data["main"]["temp"]
#     desc = data["weather"][0]["description"]
#     return f"The weather in {city} is {desc} with a temperature of {temp}°C."


# def get_news(prompt: str) -> str:
#     """
#     Example placeholder for a news API (can integrate NewsAPI.org).
#     """
#     return "News API not yet implemented."

####### to run a single file to test
# ============================================================
# File: api_items.py
# Description: Handles external API queries for SEVEN
# ============================================================
import os
import requests
import re

def get_weather(prompt: str):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "Missing OPENWEATHER_API_KEY environment variable."

    city_match = re.search(r"in ([A-Za-z\s]+)", prompt)
    city = city_match.group(1).strip() if city_match else "Toronto"

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    res = requests.get(url)
    if res.status_code != 200:
        return f"API request failed: {res.status_code}, {res.text}"

    data = res.json()
    temp = data["main"]["temp"]
    desc = data["weather"][0]["description"]
    return f"The weather in {city} is {desc} with {temp}°C."


def get_crypto_price(prompt: str):
    api_key = os.getenv("COINDESK_API_KEY")
    if not api_key:
        return "Missing COINDESK_API_KEY environment variable."

    # Default: BTC if none found
    if "ethereum" in prompt.lower():
        symbol = "ETH"
    elif "doge" in prompt.lower():
        symbol = "DOGE"
    else:
        symbol = "BTC"

    url = f"https://api.coindesk.com/v1/bpi/currentprice/{symbol.upper()}.json"
    headers = {"Authorization": f"Bearer {api_key}"}
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        return f"Crypto API failed: {res.status_code}, {res.text}"

    data = res.json()
    try:
        price = data["bpi"]["USD"]["rate"]
        return f"{symbol.upper()} is currently trading at ${price} USD."
    except KeyError:
        return f"Unexpected response format: {data}"


def get_news(prompt: str):
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return "Missing NEWS_API_KEY environment variable."

    url = f"https://newsapi.org/v2/top-headlines?country=us&pageSize=3&apiKey={api_key}"
    res = requests.get(url)
    if res.status_code != 200:
        return f"News API failed: {res.status_code}, {res.text}"

    data = res.json()
    headlines = [a["title"] for a in data.get("articles", [])[:3]]
    if not headlines:
        return "No headlines available right now."
    return "Here are the top headlines:\n- " + "\n- ".join(headlines)


def detect_api_intent(prompt: str):
    """Detects if the prompt requires an external API call."""
    text = prompt.lower()
    if any(k in text for k in ["weather", "temperature", "forecast"]):
        return "weather"
    if any(k in text for k in ["bitcoin", "crypto", "ethereum", "dogecoin"]):
        return "crypto"
    if any(k in text for k in ["news", "headline"]):
        return "news"
    return None
