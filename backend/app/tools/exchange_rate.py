import logging
import requests

from config.config import load_config

logger = logging.getLogger(__name__)

config = load_config()


class ExchangeRateTool:
    name = "get_exchange_rate"

    description = "Get the exchange rate between two currencies."

    parameters = {
        "type": "function",
        "function": {
            "name": "get_exchange_rate",
            "description": "Get the exchange rate between two currencies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_currency": {
                        "type": "string",
                        "description": "Source currency code, for example EUR",
                    },
                    "to_currency": {
                        "type": "string",
                        "description": "Target currency code, for example USD",
                    },
                },
                "required": ["from_currency", "to_currency", "amount"],
            },
        }
    }

    def __init__(self, exchange_rate_api_url: str, api_key: str):
        self.exchange_rate_api_url = exchange_rate_api_url
        self.api_key = api_key

    def run(self, from_currency: str, to_currency: str) -> str:
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        logger.info("Running exchange rate tool", extra={
                    "from_currency": from_currency, "to_currency": to_currency},)

        url = f"{self.exchange_rate_api_url}/{self.api_key}/pair/{from_currency}/{to_currency}"

        last_error = None

        for attempt in range(config["tool_calls"]["max_retries"]):
            logger.info(
                f"Attempt {attempt + 1} to get exchange rate from {from_currency} to {to_currency}")

            try:
                response = requests.get(
                    url, timeout=config["tool_calls"]["timeout"],)
                response.raise_for_status()
                data = response.json()

                if data.get("result") == "success":
                    exchange_rate = data.get("conversion_rate")

                    if exchange_rate is None:
                        raise ValueError(
                            "conversion_rate not found in API response.")

                    return (
                        f"Exchange rate from {from_currency} to {to_currency}: "
                        f"{exchange_rate}"
                    )

                raise ValueError(
                    f"API returned an error: {data.get('error-type', 'unknown error')}"
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
            f"Failed to get exchange rate after "
            f"{config['tool_calls']['max_retries']} attempts. "
            f"Last error: {last_error}"
        )
