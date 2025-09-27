import requests
import json
from typing import Optional
import os
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, retry_if_result


logger = logging.getLogger('cli_logger')


def get_gemini_key() -> Optional[str]:
    """Retrieve the Gemini API key from a local file or environment variable."""
    try:
        gemini_token = os.getenv("GEMINI_API_KEY")
        if gemini_token:
            return gemini_token
        with open('gemini_key.txt', 'r') as file:
            return file.readline().strip()
    except FileNotFoundError:
        logger.warning("Gemini API key file not found.")
        return None


@retry(
    retry=(
        retry_if_exception_type((requests.exceptions.RequestException, json.JSONDecodeError)) |
        retry_if_result(lambda result: result is None)
    ),
    wait=wait_exponential(multiplier=1, max=10),  # seconds
    stop=stop_after_attempt(3)
)
def prompt_gemini(prompt: str, api_key: str) -> Optional[str]:
    """
    Make a request to Google's Gemini API to generate responses based on a text prompt.

    Args:
        prompt (str): The text prompt to send to the model
        api_key (str): Gemini API key

    Returns:
        generated_text (str): Gemini's response
    """
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': api_key
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        generated_text = response.json()['candidates'][0]['content']['parts'][0]['text']

        return generated_text

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return None


# if __name__ == "__main__":
#     with open('gemini_key.txt', 'r') as file:
#         GEMINI_API_KEY = file.readline().strip()

#     prompt_text = "How do you say Hi in French?"

#     result = prompt_gemini(prompt_text, GEMINI_API_KEY)

#     if result:
#         try:
#             logger.debug(f"\nGenerated Response: {result}")
#         except (KeyError, IndexError) as e:
#             print(f"Error extracting response: {e}")
#     else:
#         print("Request failed")
