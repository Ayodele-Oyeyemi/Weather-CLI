# Weather CLI

A simple, dependency-free Python CLI tool that fetches current weather (and
optional forecasts) for any city, using the free [Open-Meteo](https://open-meteo.com/) API.

No API key, no signup, no third-party libraries required.

## Features

- ✅ Look up weather by city name (automatically geocoded)
- ✅ Look up weather by exact latitude/longitude
- ✅ Celsius or Fahrenheit units
- ✅ Optional multi-day forecast (up to 16 days)
- ✅ Raw JSON output option, for piping into other scripts
- ✅ Clear error messages for invalid cities or connection issues

## Requirements

- Python 3.7+
- No external dependencies (uses `urllib` from the standard library)
- An internet connection (this tool calls a live weather API)

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/weather-cli.git
cd weather-cli
```

That's it — no `pip install` needed.

## Usage

```bash
python weather.py <city> [options]
```

### Options

| Flag         | Description                                                        |
|--------------|---------------------------------------------------------------------|
| `--lat`      | Latitude (use instead of a city name)                               |
| `--lon`      | Longitude (use instead of a city name)                              |
| `--units`    | `celsius` or `fahrenheit` (default: `celsius`)                      |
| `--forecast` | Number of forecast days to include, 0-16 (default: `0`, current only)|
| `--json`     | Print raw JSON instead of a formatted summary                       |

### Examples

**Current weather for a city:**
```bash
python weather.py "Lagos"
```
```
Weather for Lagos, Nigeria

  Temperature: 29.4°C
  Conditions:  Partly cloudy
  Humidity:    78%
  Wind speed:  9.5 km/h
```

**Fahrenheit instead of Celsius:**
```bash
python weather.py "New York" --units fahrenheit
```

**3-day forecast:**
```bash
python weather.py "Tokyo" --forecast 3
```

**Look up by exact coordinates:**
```bash
python weather.py --lat 6.5244 --lon 3.3792
```

**Raw JSON output:**
```bash
python weather.py "Paris" --json
```

## How it works

1. If you pass a city name, the tool first calls Open-Meteo's free
   geocoding API to convert it into latitude/longitude.
2. It then calls the forecast API with those coordinates to fetch current
   conditions (and forecast data, if requested).
3. Weather codes returned by the API are mapped to human-readable
   descriptions (e.g. code `61` → "Slight rain").

## Running tests

Tests mock all network calls, so they run fully offline:

```bash
python -m unittest discover tests
```

## Contributing

Issues and pull requests are welcome! Ideas for future features:
- Hourly forecast breakdown
- Support for multiple cities in one call
- A `--watch` mode that refreshes periodically

## License

MIT — see [LICENSE](LICENSE).
