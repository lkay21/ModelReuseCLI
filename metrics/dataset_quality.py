from apis.gemini import *
from apis.hf_client import HFClient
import re


def compute_dataset_quality(dataset_id: str) -> float:
    '''
    Compute the quality score of 1 dataset by checking the size, descriptions, and other relevant info.
    Ask Gemini to score the datasets based on the information given. Score from 0 to 1.

    Args:
        dataset_id (str): The dataset identifier on Hugging Face
    Returns:
        score (float): The dataset quality score from 0 to 1
    '''
    hf_client = HFClient()
    
    try:
        dataset_card = hf_client.dataset_card_text(dataset_id)
    except Exception:
        # Unable to fetch dataset card as it may not exist or it is not on Hugging Face
        return 0.0

    # If dataset card is , return 0.0
    if not dataset_card:
        return 0.0

    api_key = get_gemini_key()
    if not api_key:
        return 0.0

    dataset_quality_prompt = f"""Analyze the following dataset information and its card from Hugging Face.
Dataset ID: {dataset_id}
Dataset Card:
{dataset_card if dataset_card else "No dataset card available"}
Based on the information, evaluate the dataset's quality on a scale from 0.0 to 1.0. Consider:
- Completeness and clarity of the documentation. [score out of 0.4 points]
- Size and diversity of the dataset. [score out of 0.2 points]
- Presence of data splits (train, validation, test). [score out of 0.2 points]
- Clear licensing and citation information. [score out of 0.2 points]
In your explanation, you must ALWAYS specify how many points were scored on each criteria (out of the total points listed).
Your answer should be in the following format: <score between 0-1>: <explanation and score breakdown>"""

    num_retries = 0
    max_retries = 3

    while num_retries < max_retries:
        dq_check = prompt_gemini(dataset_quality_prompt, api_key)
        match = re.match(r"([0-1](?:\.\d+)?):(.*)", dq_check, re.DOTALL)
        if match:
            score = float(match.group(1))
            explanation = match.group(2).strip()
            # print(f"Dataset Quality Explanation: {explanation}")
            break
        num_retries += 1
    else:
        raise ValueError("Could not parse the dataset quality score from the response.")
    return score

if __name__ == "__main__":
    # Example usage
    print(compute_dataset_quality("rajpurkar/squad"))