"""
Weather Data Provider - Open-Meteo API

Open-Meteo is free, open-source weather API with no API key required.
"""

import httpx
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from .base import ExternalDataProvider, ExternalDataResult

logger = logging.getLogger(__name__)


class WeatherProvider(ExternalDataProvider):
    """Weather provider using Open-Meteo API"""
    
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    def get_provider_name(self) -> str:
        return "Open-Meteo"
    
    def supports(self, intent_type: str, params: Dict[str, Any]) -> bool:
        """Check if this provider supports weather intent"""
        return intent_type == "weather"
    
    async def fetch(self, intent_type: str, params: Dict[str, Any]) -> ExternalDataResult:
        """
        Fetch weather data from Open-Meteo
        
        Args:
            intent_type: Should be "weather"
            params: Should contain "location" (city name or lat/lon)
            
        Returns:
            ExternalDataResult with weather data
        """
        if intent_type != "weather":
            return ExternalDataResult(
                data={},
                source=self.get_provider_name(),
                timestamp=datetime.utcnow(),
                cached=False,
                success=False,
                error_message=f"Invalid intent type: {intent_type}"
            )
        
        location = params.get("location")
        if not location:
            return ExternalDataResult(
                data={},
                source=self.get_provider_name(),
                timestamp=datetime.utcnow(),
                cached=False,
                success=False,
                error_message="Location parameter is required"
            )
        
        try:
            # Geocode location first (simple: try to get lat/lon from location name)
            # For MVP, we'll use a simple approach - can be improved later
            lat, lon = await self._geocode_location(location)
            
            if not lat or not lon:
                return ExternalDataResult(
                    data={},
                    source=self.get_provider_name(),
                    timestamp=datetime.utcnow(),
                    cached=False,
                    success=False,
                    error_message=f"Could not geocode location: {location}"
                )
            
            # Fetch weather data
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.BASE_URL,
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "current": "temperature_2m,relative_humidity_2m,weather_code",
                        "timezone": "auto"
                    }
                )
                
                response.raise_for_status()
                raw_data = response.json()
                
                # Parse and structure data
                current = raw_data.get("current", {})
                weather_data = {
                    "location": location,
                    "temperature": current.get("temperature_2m"),
                    "humidity": current.get("relative_humidity_2m"),
                    "weather_code": current.get("weather_code"),
                    "weather_description": self._get_weather_description(current.get("weather_code")),
                    "latitude": lat,
                    "longitude": lon,
                }
                
                return ExternalDataResult(
                    data=weather_data,
                    source=self.get_provider_name(),
                    timestamp=datetime.utcnow(),
                    cached=False,
                    raw_response=response.text,
                    success=True
                )
                
        except httpx.TimeoutException:
            return ExternalDataResult(
                data={},
                source=self.get_provider_name(),
                timestamp=datetime.utcnow(),
                cached=False,
                success=False,
                error_message="Request timeout"
            )
        except httpx.HTTPStatusError as e:
            return ExternalDataResult(
                data={},
                source=self.get_provider_name(),
                timestamp=datetime.utcnow(),
                cached=False,
                success=False,
                error_message=f"HTTP error: {e.response.status_code}"
            )
        except Exception as e:
            logger.error(f"Weather API error: {e}", exc_info=True)
            return ExternalDataResult(
                data={},
                source=self.get_provider_name(),
                timestamp=datetime.utcnow(),
                cached=False,
                success=False,
                error_message=f"Error: {str(e)}"
            )
    
    async def _geocode_location(self, location: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Geocode location name to lat/lon
        
        For MVP, we'll use Open-Meteo's geocoding API
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://geocoding-api.open-meteo.com/v1/search",
                    params={
                        "name": location,
                        "count": 1,
                        "language": "en",
                        "format": "json"
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                results = data.get("results", [])
                if results:
                    first_result = results[0]
                    return (first_result.get("latitude"), first_result.get("longitude"))
                
                return (None, None)
                
        except Exception as e:
            logger.warning(f"Geocoding error for {location}: {e}")
            return (None, None)
    
    def _get_weather_description(self, weather_code: Optional[int]) -> str:
        """Convert WMO weather code to description"""
        if weather_code is None:
            return "Unknown"
        
        # WMO Weather interpretation codes (WW)
        # Simplified mapping for MVP
        code_map = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
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
        
        return code_map.get(weather_code, f"Weather code {weather_code}")

