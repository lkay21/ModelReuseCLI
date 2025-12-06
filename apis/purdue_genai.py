import requests
import json
from typing import Optional
import os
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, retry_if_result


logger = logging.getLogger('cli_logger')


# # For Testing: Load environment variables from .env file
# from dotenv import load_dotenv
# load_dotenv()  # reads .env file into environment variables
# # REMOVE ABOVE LINES IN PRODUCTION


def get_purdue_genai_key() -> Optional[str]:
    """
    Retrieve the Purdue GenAI Studio API key from a local file or environment variable.
    Returns:
        api_key (str): The API key if found, else None
    """
    try:
        genai_token = os.getenv("GEN_AI_STUDIO_API_KEY")
        try:
            # If it's a JSON string, extract the actual key
            if genai_token.startswith("{"):
                import json
                parsed = json.loads(genai_token)
                genai_token = parsed.get("GEN_AI_STUDIO_API_KEY", genai_token)
            
            logger.info(f"API key loaded successfully, length: {len(genai_token)}")
            logger.debug(f"Purdue GenAI Studio API Key: {genai_token}")
        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"Error parsing API key: {e}")
            
        if genai_token:
            return genai_token
        with open('purdue_genai_key.txt', 'r') as file:
            return file.readline().strip()
    except FileNotFoundError:
        logger.warning("Purdue GenAI Studio API key file not found.")
        return None
    
@retry(
    retry=(
        retry_if_exception_type((requests.exceptions.RequestException, json.JSONDecodeError, Exception)) |
        retry_if_result(lambda result: result is None)
    ),
    wait=wait_exponential(multiplier=1, max=10),
    stop=stop_after_attempt(3)
)
def prompt_purdue_genai(prompt: str, api_key: str) -> Optional[str]:
    """
    Make a request to Purdue's GenAI Studio API to generate responses based on a text prompt.
    Args:
        prompt (str): The text prompt to send to the model
        api_key (str): Purdue GenAI Studio API key
    Returns:
        generated_text (str): GenAI Studio's response
    """

    url = "https://genai.rcac.purdue.edu/api/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "llama4:latest",
        "messages": [
        {
            "role": "user",
            "content": prompt
        }
        ],
        "stream": False
    }
    response = requests.post(url, headers=headers, json=body)
    data = response.json()
    if response.status_code == 200:
        return(data["choices"][0]["message"]["content"])
    else:
        logger.error(f"Error: {response.status_code}, {response.text}")
        # raise Exception(f"Error: {response.status_code}, {response.text}")
    
# if __name__ == "__main__":
#     # Example usage
#     api_key = get_purdue_genai_key()
#     if api_key:
#         prompt = "Hello, how are you?"
#         response = prompt_purdue_genai(prompt, api_key)
#         print("Response from Purdue GenAI Studio:", response)
    