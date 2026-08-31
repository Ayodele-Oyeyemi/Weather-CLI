#!/usr/bin/env python3
"""
weather.py

A simple CLI tool to fetch current weather (and optional forecast) for any
city, using the free Open-Meteo API. No API key or signup required.

Supports:
  - Looking up weather by city name (auto geocoded to coordinates)
  - Looking up weather directly by latitude/longitude
  - Celsius or Fahrenheit units
  - Optional multi-day forecast
  - JSON output (for piping into other tools/scripts)

Usage examples:
  # Current weather for a city
  python weather.py "Lagos"

  # Current weather for a city, in Fahrenheit
  python weather.py "New York" --units fahrenheit

  # 3-day forecast
  python weather.py "Tokyo" --forecast 3

  # Look up by exact coordinates instead of a city name
  python weather.py --lat 6.5244 --lon 3.3792

  # Raw JSON output instead of a formatted summary
  python weather.py "Paris" --json
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather codes -> human-readable description
# https://open-meteo.com/en/docs (see "Weather variable documentation")
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch current weather (and optional forecast) for a city."
    )
    parser.add_argument(
        "city", type=str, nargs="?", default=None,
        help="City name to look up (e.g. 'Lagos', 'New York')",
    )
    parser.add_argument(
        "--lat", type=float, default=None,
        help="Latitude (use instead of city name)",
    )
    parser.add_argument(
        "--lon", type=float, default=None,
        help="Longitude (use instead of city name)",
    )
    parser.add_argument(
        "--units", type=str, choices=["celsius", "fahrenheit"], default="celsius",
        help="Temperature units (default: celsius)",
    )
    parser.add_argument(
        "--forecast", type=int, default=0,
        help="Number of forecast days to include (0-16, default: 0 = current weather only)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Print raw JSON instead of a formatted summary",
    )
    return parser.parse_args()


def fetch_json(url: str, params: dict) -> dict:
    """Fetch a URL with query params and return parsed JSON, or exit with a clear error."""
    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"

    try:
        with urllib.request.urlopen(full_url, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"Error: could not reach the weather service ({e.reason}).")
        print("Check your internet connection and try again.")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: received an unexpected response from the weather service.")
        sys.exit(1)


def geocode_city(city: str):
    """Look up a city name and return (name, country, lat, lon), or None if not found."""
    data = fetch_json(GEOCODING_URL, {"name": city, "count": 1})
    results = data.get("results")
    if not results:
        return None

    place = results[0]
    return {
        "name": place.get("name"),
        "country": place.get("country"),
        "lat": place.get("latitude"),
        "lon": place.get("longitude"),
    }


def get_weather(lat: float, lon: float, units: str, forecast_days: int) -> dict:
    temp_unit = "fahrenheit" if units == "fahrenheit" else "celsius"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
        "temperature_unit": temp_unit,
        "timezone": "auto",
    }
    if forecast_days > 0:
        params["daily"] = "weather_code,temperature_2m_max,temperature_2m_min"
        params["forecast_days"] = min(forecast_days, 16)

    return fetch_json(FORECAST_URL, params)


def describe_code(code: int) -> str:
    return WEATHER_CODES.get(code, f"Unknown conditions (code {code})")


def print_summary(location_label: str, data: dict, units: str, forecast_days: int):
    unit_symbol = "°F" if units == "fahrenheit" else "°C"
    current = data.get("current", {})

    print(f"Weather for {location_label}\n")
    print(f"  Temperature: {current.get('temperature_2m')}{unit_symbol}")
    print(f"  Conditions:  {describe_code(current.get('weather_code'))}")
    print(f"  Humidity:    {current.get('relative_humidity_2m')}%")
    print(f"  Wind speed:  {current.get('wind_speed_10m')} km/h")

    if forecast_days > 0:
        daily = data.get("daily", {})
        dates = daily.get("time", [])
        codes = daily.get("weather_code", [])
        highs = daily.get("temperature_2m_max", [])
        lows = daily.get("temperature_2m_min", [])

        print(f"\n{forecast_days}-day forecast:")
        for date, code, high, low in zip(dates, codes, highs, lows):
            print(f"  {date}: {describe_code(code)}, high {high}{unit_symbol} / low {low}{unit_symbol}")


def main():
    args = parse_args()

    if args.lat is not None and args.lon is not None:
        lat, lon = args.lat, args.lon
        location_label = f"({lat}, {lon})"
    elif args.city:
        place = geocode_city(args.city)
        if not place:
            print(f"Error: could not find a location matching '{args.city}'.")
            sys.exit(1)
        lat, lon = place["lat"], place["lon"]
        location_label = f"{place['name']}, {place['country']}"
    else:
        print("Error: provide a city name, or both --lat and --lon.")
        sys.exit(1)

    data = get_weather(lat, lon, args.units, args.forecast)

    if args.json:
        print(json.dumps(data, indent=2))
        return

    print_summary(location_label, data, args.units, args.forecast)


if __name__ == "__main__":
    main()
