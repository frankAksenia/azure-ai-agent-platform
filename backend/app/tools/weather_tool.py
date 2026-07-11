import logging
import requests

logger = logging.getLogger(__name__)


class WeatherTool:
    name = "get_weather"

    description = "Get the current weather for a given location."

    parameters = {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "The city name, for example Seattle, London, or Tokyo.",
            },
        },
        "required": ["city"],
        "additionalProperties": False,
    }

    def __init__(self, weather_api_url: str, api_key: str, config: dict):
        self.weather_api_url = weather_api_url
        self.api_key = api_key
        self.config = config

    def run(self, city: str) -> str:
        logger.info("Running weather tool", extra={"city": city})

        url = f"{self.weather_api_url}?q={city}&appid={self.api_key}&units=metric"

        last_error = None

        for attempt in range(self.config["tool_calls"]["max_retries"]):
            logger.info(
                f"Attempt {attempt + 1} to get weather data for {city}")

            try:
                response = requests.get(
                    url,
                    timeout=self.config["tool_calls"]["timeout"],
                )
                response.raise_for_status()
                data = response.json()

                weather = data.get("weather")
                main = data.get("main")

                if not weather or not main:
                    raise ValueError(f"Unexpected response format: {data}")

                weather_description = weather[0].get("description")
                temperature = main.get("temp")

                if weather_description is None or temperature is None:
                    raise ValueError(
                        f"Missing weather description or temperature: {data}")

                return (
                    f"The current weather in {city} is {weather_description} "
                    f"with a temperature of {temperature}°C."
                )

            except requests.exceptions.Timeout:
                last_error = f"Request timed out on attempt {attempt + 1}."
                logger.warning(last_error)

            except requests.exceptions.RequestException as e:
                last_error = f"Request failed on attempt {attempt + 1}: {e}"
                logger.warning(last_error)

            except ValueError as e:
                last_error = f"Value error on attempt {attempt + 1}: {e}"
                logger.warning(last_error)

        return (
            f"Failed to get weather data for {city} after "
            f"{self.config['tool_calls']['max_retries']} attempts. "
            f"Last error: {last_error}"
        )
