import logging
import sys
from typing import Dict
from apis.gemini import get_gemini_key
from apis.purdue_genai import get_purdue_genai_key


logger = logging.getLogger('cli_logger')


def get_prompt_key() -> Dict[str, str]:
    """
    Obtain prompting API key - either Purdue GenAI Studio or Gemini.

    Returns:
        key (Dict): Dictionary containing the API key
    """
    logger.info("Compiling API key from available sources...")
    keys = {}

    # Purdue GenAI Studio and Gemini
    purdue_genai_token = get_purdue_genai_key()
    logger.info(f"Purdue GenAI Studio key found: {purdue_genai_token}")
    if purdue_genai_token:
        logger.info("Using Purdue GenAI Studio API key for prompting.")
    else:
        logger.warning("API key not found")
        gemini_api_key = get_gemini_key()

    if purdue_genai_token:
        return {"purdue_genai": purdue_genai_token}
    elif gemini_api_key:
        return {"gemini": gemini_api_key}
    
    if not purdue_genai_token and not gemini_api_key:
        logger.error("No API keys found for Gemini or Purdue GenAI Studio. Exiting.")
        sys.exit(1)
