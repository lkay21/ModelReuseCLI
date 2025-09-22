from apis.gemini import *
from apis.hf_client import HFClient


def compute_dataset_quality(dataset_id: str) -> float:
    '''
    Compute the quality score of 1 datasetby checking the size, descriptions, and other relevant info.
    Ask Gemini to score the datasets based on the information given. Score from 0 to 1.

    Args:
        dataset_id (str): The dataset identifier on Hugging Face
    Returns:
        score (float): The dataset quality score from 0 to 1
    '''
    hf_client = HFClient()
    dataset_info = hf_client.dataset_info(dataset_id)
    dataset_card = hf_client.dataset_card_text(dataset_id)

    api_key = get_gemini_key()
    if not api_key:
        return 0.0

    prompt = f"""Analyze the following dataset information and its card from Hugging Face.

Dataset ID: {dataset_id}
Dataset Info: {dataset_info}
Dataset Card:
{dataset_card[:8000] if dataset_card else "No dataset card available"}

Based on the information, evaluate the dataset's quality on a scale from 0.0 to 1.0. Consider:
- Completeness and clarity of the description.
- Presence of data splits (train, validation, test).
- Clear licensing and citation information.
- General usability and documentation.

Respond with ONLY the final score as a single float in the format x.xx
Response:"""

    try:
        response = prompt_gemini(prompt, api_key)
        if response:
            score = float(response.strip().split('\\n')[-1])  # take just the last line, in case of extra output
            return score
    except (ValueError, IndexError):
        return 0.0
    except Exception as e:
        print(f"An error occurred during Gemini API call for dataset quality: {e}")
        return 0.0

    return 0.0



def compute_avg_dataset_quality(dataset_ids: list) -> float:
    '''
    Compute the average quality score of all datasets for a given model.

    Args:
        dataset_ids (list): A list of dataset identifiers on Hugging Face
    Returns:
        avg_score (float): The average dataset quality score from 0 to 1
    '''
    if len(dataset_ids) == 0:
        return 0.0
    dataset_scores = []
    for dataset_id in dataset_ids:
        dataset_scores.append(compute_dataset_quality(dataset_id))
    avg_score = sum(dataset_scores) / len(dataset_scores)
    return avg_score

