from apis.hf_client import HFClient
from apis.gemini import prompt_gemini, get_gemini_key
from apis.purdue_genai import get_purdue_genai_key, prompt_purdue_genai
from utils.prompt_key import get_prompt_key
import re
import logging


logger = logging.getLogger('cli_logger')


def performance_claims(model_id: str) -> float:
    client = HFClient()
    model_card = client.model_card_text(model_id)
    
    prompt_key = get_prompt_key()
    if 'purdue_genai' in prompt_key:
        prompt_function = prompt_purdue_genai
        api_key = get_purdue_genai_key()
    elif 'gemini' in prompt_key:
        prompt_function = prompt_gemini
        api_key = get_gemini_key()

    res = prompt_function(f"Read the following model card of a HuggingFaceModel. " \
                    "Evaluate on a float scale of 0 to 1 the claimed performance of the model. " \
                    "Assign 0.33 points if there is benchmarking data present " \
                    "and another 0.33 points if there are testing scores present "\
                    ", add another 0.1 points for presence of other performance claims." \
                    "and another 0.24 if the card contains specific and data-backed claims (partial credit is allowed for this 0.24)" \
                    "Reply ONLY with the total score float in the format x.xx. No other words or characters except the float" \
                    f"{model_card}", api_key)
    logger.debug(f"performance claims explanation: {res}")
    try:
        score = float(res.rstrip())
        return score
    except Exception as e:
        logger.error(f"ERROR: Could not parse performance claims score from LLM response. Exception: {e}")
        return 0

