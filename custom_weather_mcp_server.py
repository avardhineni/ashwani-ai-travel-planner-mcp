"""An original local MCP server exposing OpenWeatherMap tools over stdio."""
from __future__ import annotations

import os
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()
mcp = FastMCP('Travel Planner Weather Server')
BASE_URL = 'https://api.openweathermap.org/data/2.5'


def _openweather(endpoint: str, city: str) -> dict:
    if not city or not city.strip():
        return {'error': 'City is required'}
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if not api_key:
        return {'error': 'Weather API key not configured'}
    try:
        response = requests.get(
            f'{BASE_URL}/{endpoint}',
            params={'q': city.strip(), 'appid': api_key, 'units': 'metric'},
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        # Avoid echoing request URLs/credentials into tool output.
        return {'error': f'OpenWeatherMap request failed: {type(exc).__name__}'}
    except ValueError:
        return {'error': 'OpenWeatherMap returned invalid JSON'}


@mcp.tool()
def get_current_weather(city: str) -> dict:
    """Get current weather for a city. Not a forecast for a future trip date."""
    data = _openweather('weather', city)
    if 'error' in data:
        return data
    try:
        return {
            'city': data['name'],
            'temperature_c': data['main']['temp'],
            'feels_like_c': data['main']['feels_like'],
            'humidity_percent': data['main']['humidity'],
            'condition': data['weather'][0]['description'],
            'wind_speed_mps': data['wind']['speed'],
            'data_type': 'current_weather',
        }
    except (KeyError, IndexError, TypeError):
        return {'error': 'Unexpected current weather response structure'}


@mcp.tool()
def get_forecast(city: str) -> dict:
    """Get first 5 three-hour forecast points (about 15 hours), not a 5-day itinerary forecast."""
    data = _openweather('forecast', city)
    if 'error' in data:
        return data
    try:
        points = [
            {
                'datetime_utc': item['dt_txt'],
                'temperature_c': item['main']['temp'],
                'condition': item['weather'][0]['description'],
            }
            for item in data['list'][:5]
        ]
        return {'city': city, 'data_type': 'three_hour_forecast', 'forecast_points': points}
    except (KeyError, IndexError, TypeError):
        return {'error': 'Unexpected forecast response structure'}


if __name__ == '__main__':
    mcp.run(transport='stdio')
