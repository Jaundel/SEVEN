"""Real-world energy equivalents for SEVEN energy savings.

This module converts saved watt-hours into relatable everyday comparisons,
helping users understand the impact of intelligent routing decisions.
All conversion factors are based on typical real-world power consumption.
"""

from __future__ import annotations

import random
from typing import TypedDict


class EnergyEquivalent(TypedDict):
    """Structure for a single energy equivalent."""

    unit: str
    wh_per_unit: float
    format_str: str
    emoji: str


# Real-world energy equivalents with researched conversion factors
EQUIVALENTS: list[EnergyEquivalent] = [
    {
        "unit": "LED bulb (10W)",
        "wh_per_unit": 10.0,
        "format_str": "You've powered a LED bulb for {:.1f} hours",
        "emoji": "💡",
    },
    {
        "unit": "smartphone charge",
        "wh_per_unit": 12.0,
        "format_str": "You've charged a smartphone {:.2f} times",
        "emoji": "📱",
    },
    {
        "unit": "laptop work (50W)",
        "wh_per_unit": 50.0,
        "format_str": "You've powered a laptop for {:.1f} hours",
        "emoji": "💻",
    },
    {
        "unit": "Wi-Fi router (6W)",
        "wh_per_unit": 6.0,
        "format_str": "You've kept Wi-Fi running for {:.1f} hours",
        "emoji": "📡",
    },
    {
        "unit": "TV streaming (100W)",
        "wh_per_unit": 100.0,
        "format_str": "You've streamed TV for {:.1f} hours",
        "emoji": "📺",
    },
    {
        "unit": "coffee brew (800W for 5min)",
        "wh_per_unit": 66.7,
        "format_str": "You've brewed {:.1f} cups of coffee",
        "emoji": "☕",
    },
    {
        "unit": "microwave heating (1000W)",
        "wh_per_unit": 16.7,
        "format_str": "You've microwaved food for {:.0f} minutes",
        "emoji": "🍲",
    },
    {
        "unit": "electric kettle boil (2000W for 3min)",
        "wh_per_unit": 100.0,
        "format_str": "You've boiled water {:.1f} times",
        "emoji": "🫖",
    },
    {
        "unit": "desktop PC (200W)",
        "wh_per_unit": 200.0,
        "format_str": "You've powered a desktop PC for {:.1f} hours",
        "emoji": "🖥️",
    },
    {
        "unit": "gaming console (150W)",
        "wh_per_unit": 150.0,
        "format_str": "You've gamed for {:.1f} hours",
        "emoji": "🎮",
    },
    {
        "unit": "tablet charge (18Wh)",
        "wh_per_unit": 18.0,
        "format_str": "You've charged a tablet {:.2f} times",
        "emoji": "📱",
    },
    {
        "unit": "room fan (75W)",
        "wh_per_unit": 75.0,
        "format_str": "You've run a fan for {:.1f} hours",
        "emoji": "🌀",
    },
    {
        "unit": "e-bike mile (15Wh/mi)",
        "wh_per_unit": 15.0,
        "format_str": "You've e-biked {:.1f} miles",
        "emoji": "🚴",
    },
    {
        "unit": "EV mile (300Wh/mi)",
        "wh_per_unit": 300.0,
        "format_str": "You've offset {:.2f} miles of EV driving",
        "emoji": "🚗",
    },
    {
        "unit": "CO₂ (0.4 kg/kWh grid avg)",
        "wh_per_unit": 2500.0,
        "format_str": "You've prevented {:.1f}g of CO₂",
        "emoji": "🌍",
    },
]


def random_equivalent(saved_wh: float) -> str:
    """Convert saved watt-hours into a random real-world equivalent.

    Args:
        saved_wh: Total watt-hours saved through intelligent routing.

    Returns:
        A human-readable string describing the energy savings in relatable terms.
        Returns a fallback message if saved_wh is zero or negative.

    Examples:
        >>> random_equivalent(25.0)
        '💡 You've powered a LED bulb for 2.5 hours'
        >>> random_equivalent(100.0)
        '☕ You've brewed 1.5 cups of coffee'
        >>> random_equivalent(0.0)
        'Start chatting to make an impact!'
    """
    if saved_wh <= 0:
        return "Start chatting to make an impact!"

    # Pick a random equivalent
    eq = random.choice(EQUIVALENTS)

    # Calculate the value
    value = saved_wh / eq["wh_per_unit"]

    # Format based on the conversion factor
    # Use custom formatting for very small or very large values
    if value < 0.01:
        return f"{eq['emoji']} You've saved just a few seconds worth"
    elif value > 1000:
        return f"{eq['emoji']} You've made a HUGE impact!"
    else:
        return f"{eq['emoji']} {eq['format_str'].format(value)}"


__all__ = ["random_equivalent", "EQUIVALENTS", "EnergyEquivalent"]
