from apis.gemini import *
from apis.hf_client import HFClient
import re
import logging


logger = logging.getLogger('cli_logger')


def license_score(model_id: str, api_key: str) -> float:
    """
    Evaluate the license compliance of the model using Gemini API to inspect the README content or model card license information.
    Args:
        model_id (str): The Hugging Face model ID
        api_key (str): Gemini API key
    Returns:
        score (float): License compliance score between 0 and 1
    """
    client = HFClient()
    modelcard_license = client.model_info(model_id).get("license", "No license information found on model card.")

    model_info = client.model_info(model_id)

    readme_text = client.model_card_text(model_id)
    license_info = prompt_gemini(
        f"Extract all license-related information from the following README content:\n{readme_text}. If no license information is found, respond with 'No license information found in README'.",
        api_key
    )

    if "No license information found" in modelcard_license:
        license_compatibility_prompt = f'''Based on the following license information of a model, determine the license score on a scale of 0 to 1:\n{license_info}
        If the license is not explicitly mentioned, consider common open-source licenses and their compatibility with LGPLv2.1. Evaluate the information on its clarity & permissiveness (0.5 points) and compatibility with the LGPLv2.1 license (0.5 points). In your explanation, you must ALWAYS specify how many points were scored on each criteria (out of 0.5 points). Your answer should be in the following format: <score between 0-1>: <explanation and score breakdown>
        '''
    else:
        license_compatibility_prompt = f'''Based on the following license information of a model, determine the license score on a scale of 0 to 1:\n{modelcard_license}:{license_info}
        If the license is not explicitly mentioned, consider common open-source licenses and their compatibility with LGPLv2.1. Evaluate the information on its clarity & permissiveness (0.5 points) and compatibility with the LGPLv2.1 license (0.5 points). In your explanation, you must ALWAYS specify how many points were scored on each criteria (out of 0.5 points). Your answer should be in the following format: <score between 0-1>: <explanation and score breakdown>
        '''

    num_retries = 0
    max_retries = 3

    while num_retries < max_retries:
        license_compatibility = prompt_gemini(license_compatibility_prompt, api_key)
        match = re.match(r"([0-1](\.\d+)?):\s*(.*)", license_compatibility)
        if match:
            score = float(match.group(1))
            explanation = match.group(3)
            logger.debug(f"License Score Explanation for {model_id}: {explanation}")
            break
        num_retries += 1
    else:
        logger.error("Could not parse the license score from the response.")
        raise ValueError("Could not parse the license score from the response.")
    return score


# if __name__ == "__main__":
#     api_key = get_gemini_key()

#     model_id = "meta-llama/Meta-Llama-3-8B"
#     l_score, explanation = license_score(model_id, api_key)
#     print(f"License Score for {model_id}: {l_score}")
#     print(f"Explanation: {explanation}")
