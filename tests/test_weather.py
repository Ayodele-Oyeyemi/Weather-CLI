"""
Tests for weather.py.

These tests mock all network calls (via unittest.mock), so they run offline
and don't depend on the real Open-Meteo API being reachable.

Run with:
    python -m unittest discover tests
or:
    python tests/test_weather.py
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from weather import describe_code, geocode_city, get_weather, WEATHER_CODES


class TestDescribeCode(unittest.TestCase):
    def test_known_code(self):
        self.assertEqual(describe_code(0), "Clear sky")
        self.assertEqual(describe_code(95), "Thunderstorm")

    def test_unknown_code(self):
        self.assertIn("Unknown conditions", describe_code(9999))


class TestGeocodeCity(unittest.TestCase):
    @patch("weather.fetch_json")
    def test_found(self, mock_fetch):
        mock_fetch.return_value = {
            "results": [
                {"name": "Lagos", "country": "Nigeria", "latitude": 6.5244, "longitude": 3.3792}
            ]
        }
        result = geocode_city("Lagos")
        self.assertEqual(result["name"], "Lagos")
        self.assertEqual(result["country"], "Nigeria")
        self.assertAlmostEqual(result["lat"], 6.5244)
        self.assertAlmostEqual(result["lon"], 3.3792)

    @patch("weather.fetch_json")
    def test_not_found(self, mock_fetch):
        mock_fetch.return_value = {"results": []}
        result = geocode_city("Nowhereville")
        self.assertIsNone(result)

    @patch("weather.fetch_json")
    def test_missing_results_key(self, mock_fetch):
        mock_fetch.return_value = {}
        result = geocode_city("Nowhereville")
        self.assertIsNone(result)


class TestGetWeather(unittest.TestCase):
    @patch("weather.fetch_json")
    def test_current_only(self, mock_fetch):
        mock_fetch.return_value = {
            "current": {
                "temperature_2m": 28.5,
                "relative_humidity_2m": 70,
                "weather_code": 1,
                "wind_speed_10m": 12.0,
            }
        }
        data = get_weather(6.5244, 3.3792, units="celsius", forecast_days=0)
        self.assertEqual(data["current"]["temperature_2m"], 28.5)

        # Confirm forecast params were NOT included in the request when forecast_days=0
        called_params = mock_fetch.call_args[0][1]
        self.assertNotIn("daily", called_params)

    @patch("weather.fetch_json")
    def test_with_forecast(self, mock_fetch):
        mock_fetch.return_value = {"current": {}, "daily": {}}
        get_weather(6.5244, 3.3792, units="fahrenheit", forecast_days=3)

        called_params = mock_fetch.call_args[0][1]
        self.assertIn("daily", called_params)
        self.assertEqual(called_params["forecast_days"], 3)
        self.assertEqual(called_params["temperature_unit"], "fahrenheit")

    @patch("weather.fetch_json")
    def test_forecast_days_capped_at_16(self, mock_fetch):
        mock_fetch.return_value = {"current": {}, "daily": {}}
        get_weather(6.5244, 3.3792, units="celsius", forecast_days=30)

        called_params = mock_fetch.call_args[0][1]
        self.assertEqual(called_params["forecast_days"], 16)


if __name__ == "__main__":
    unittest.main()
