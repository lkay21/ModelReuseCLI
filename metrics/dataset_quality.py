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

    return 0.0 # dummy return for now



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
    
