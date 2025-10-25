"""
Weather Tool - Example tool for XandAI CLI

This is a demonstration tool that shows how to create custom tools.
In a real implementation, this would call a weather API.
"""

from datetime import datetime


class WeatherTool:
    """Get weather information for a location."""

    @staticmethod
    def get_name():
        """Return the tool's name."""
        return "weather_tool"

    @staticmethod
    def get_description():
        """Return description of what the tool does."""
        return "Get current weather information for any location"

    @staticmethod
    def get_parameters():
        """Return the parameters this tool accepts."""
        return {
            "location": "string (required) - City or location name (e.g., 'Los Angeles', 'New York')",
            "date": "string (optional) - Date for weather (default: 'now' for current weather)",
        }

    def execute(self, location: str, date: str = "now"):
        """
        Execute the weather lookup.

        Args:
            location: City or location name
            date: Date for weather forecast (default: now)

        Returns:
            Dictionary with weather information
        """
        # Simulate weather data (in real implementation, call weather API)
        # For demo purposes, return mock data

        mock_weather_data = {
            "los angeles": {
                "temperature": 25,
                "temperature_unit": "C",
                "condition": "sunny",
                "humidity": 45,
                "wind_speed": 10,
            },
            "new york": {
                "temperature": 15,
                "temperature_unit": "C",
                "condition": "cloudy",
                "humidity": 65,
                "wind_speed": 15,
            },
            "london": {
                "temperature": 12,
                "temperature_unit": "C",
                "condition": "rainy",
                "humidity": 80,
                "wind_speed": 20,
            },
            "tokyo": {
                "temperature": 20,
                "temperature_unit": "C",
                "condition": "partly cloudy",
                "humidity": 55,
                "wind_speed": 8,
            },
        }

        # Normalize location for lookup
        location_key = location.lower().strip()

        # Get weather data or default
        weather = mock_weather_data.get(
            location_key,
            {
                "temperature": 22,
                "temperature_unit": "C",
                "condition": "clear",
                "humidity": 50,
                "wind_speed": 12,
            },
        )

        # Build response
        result = {
            "location": location,
            "date": date if date != "now" else datetime.now().strftime("%Y-%m-%d"),
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "weather": weather,
            "source": "mock_weather_api (demo)",
        }

        return result
