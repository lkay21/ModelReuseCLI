"""
URL Parser for ModelReuseCLI
Handles parsing URL files and creating Model, Code, Dataset objects
"""

import re
from typing import List, Tuple, Dict
from model import Model, Code, Dataset
import logging
from apis.purdue_genai import prompt_purdue_genai
from utils.prompt_key import get_prompt_key


logger = logging.getLogger('cli_logger')


def classify_url(url: str) -> str:
    """
    Classify a URL by its type
    
    Args:
        url (str): The URL to classify
        
    Returns:
        str: 'code', 'dataset', 'model', 'empty' or 'check'
    """
    logger.debug(f"Classifying URL: {url}")
    if not url or not url.strip():
        return 'empty'
    
    url = url.strip()
    
    # GitHub patterns
    # hugging face code space ex: huggingface.co/spaces/abidlabs/en2fr
    # GitHub code pattern
    if re.search(r'github\.com', url, re.IGNORECASE):
        return 'github'

    # GitLab code pattern
    if re.search(r'gitlab\.[^/]+', url, re.IGNORECASE):
        return 'gitlab'

    # HuggingFace Spaces (code) pattern
    if re.search(r'huggingface\.co/spaces/', url, re.IGNORECASE):
        return 'hfspace'
    
    # HuggingFace dataset patterns
    if re.search(r'huggingface\.co/datasets/', url, re.IGNORECASE):
        return 'dataset'
    
    # HuggingFace model patterns (exclude spaces and datasets explicitly)
    if (re.search(r'huggingface\.co/', url, re.IGNORECASE) and 
        not re.search(r'huggingface\.co/(spaces|datasets)/', url, re.IGNORECASE)):
        return 'model'
    
    return 'check'


def extract_name_from_url(url: str) -> Tuple[str, str]:
    """
    Extract a name from a URL
    
    Args:
        url (str): The URL
        
    Returns:
        str: Extracted name or empty string if extraction fails
    """
    logger.debug(f"Extracting name from URL: {url}")
    if not url:
        return "", ""
    
    # code pattern: github/gitlab/hfspace
    github_match = re.search(r'github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/.*)?$', url, re.IGNORECASE)
    if github_match:
        owner, repo = github_match.groups()
        return owner, repo.replace('.git', '')

    gitlab_match = re.search(r'(?:git@|https?://)gitlab\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?$', url, re.IGNORECASE)
    if gitlab_match:
        return gitlab_match.group('owner'), gitlab_match.group('repo')

    hfcode_match = re.search(r'^https?://(?:www\.)?huggingface\.co/spaces/(?P<owner>[^/]+)/(?P<space>[^/]+)(?:/.*)?$', url, re.IGNORECASE)
    if hfcode_match:
        return hfcode_match.group('owner'), hfcode_match.group('space')

    # HuggingFace pattern: extract model/dataset name
    hf_match = re.search(r'huggingface\.co/(?:datasets/)?([^/]+)/([^/]+?)(?:/.*)?$', url, re.IGNORECASE)
    if hf_match:
        namespace, name = hf_match.groups()
        return namespace, name
    
    return "", ""


def populate_code_info(code: Code, code_type: str) -> None:
    """
    Populate Code object with additional information from GitHub API
    
    Args:
        code (Code): Code object to populate
    """
    # Extract name from URL
    # extract_name_from_url returns a tuple (owner, name)
    _, code._name = extract_name_from_url(code._url)
    code.type = code_type
    # TODO: Add GitHub API calls to populate metadata
    # Example implementation for metrics teams:
    # from apis.git_api import get_contributors, get_commit_history
    # owner, repo = extract_github_owner_repo(code._url)
    # code._metadata = {
    #     'contributors': get_contributors(owner, repo),
    #     'commits': get_commit_history(owner, repo),
    #     'bus_factor_data': {...}
    # }


def populate_dataset_info(dataset: Dataset) -> None:
    """
    Populate Dataset object with additional information from HuggingFace API
    
    Args:
        dataset (Dataset): Dataset object to populate
    """
    # Extract name from URL
    owner, name = extract_name_from_url(dataset._url)
    dataset._name = owner + "/" + name
    # TODO: Add HuggingFace API calls to populate metadata
    # Example implementation for metrics teams:
    # from apis.hf_client import HFClient
    # hf_client = HFClient()
    # dataset._metadata = {
    #     'dataset_info': hf_client.dataset_info(dataset._name),
    #     'downloads': ..., 'license': ..., 'size': ...
    # }


def populate_model_info(model: Model) -> None:
    """
    Populate Model object with additional information from HuggingFace API
    
    Args:
        model (Model): Model object to populate
    """
    # Extract name from URL
    owner, model.name = extract_name_from_url(model.url)
    model.id = owner + "/" + model.name
    # TODO: Add HuggingFace API calls to populate hfAPIData
    # Example implementation for metrics teams:
    # from apis.hf_client import HFClient
    # hf_client = HFClient()
    # model.hfAPIData = {
    #     'model_info': hf_client.model_info(model.name),
    #     'downloads': ..., 'license': ..., 'size': ...
    # }

def is_dataset_url_llm(url: str) -> Tuple[bool, str]:
    """
    Uses the Purdue GenAI LLM to determine if a URL points to a dataset.

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if the URL is a dataset, False otherwise.
    """
    try:
        # Create a very specific prompt for a reliable yes/no answer
        prompt = (
            f"Analyze the following URL: {url}. "
            "The URL might point to a machine learning dataset on a platform like Kaggle, Zenodo, or a university website. "
            "Respond with two lines. On line 1, the name of the dataset or 'None'. On line 2, only the word 'yes' or 'no'. Do not use any punctuation. Is this a valid link to a dataset?"
        )
        
            # "Please explain your reasoning briefly in two sentences whether the link points to a dataset or not."
        key = get_prompt_key()
        if 'purdue_genai' in key:
            response = prompt_purdue_genai(prompt, key['purdue_genai'])
        
        # Clean up the response and check for 'yes'
        if response and response.strip().splitlines()[-1].strip().lower() == 'yes':
            return True, response.strip().splitlines()[0].strip()  # Return True and dataset name if available
    except Exception as e:
        # If the API call fails for any reason, assume it's not a dataset
        logger.debug(f"LLM validation failed for {url}: {e}") 

    return False, None

def parse_URL_file(file_path: str) -> Tuple[List[Model], Dict[str, Dataset]]:
    """
    Parse a URL file and create Model objects with linked Code and Dataset objects.
    Also return a registry of all datasets encountered.
    
    Args:
        file_path (str): Path to the URL file
        
    Returns:
        Tuple[List[Model], Dict[str, Dataset]]: List of Model objects and dataset registry
    """
    models = []
    dataset_registry = {}  # Track all datasets by name
    
    try:
        logger.info(f"Parsing URL file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()

                # Parse the CSV line
                parts = [part.strip() for part in line.split(',')]
                
                # Ensure we have exactly 3 parts
                if len(parts) != 3:
                    logger.warning(f"Warning: Line {line_num} does not have exactly 3 columns: {line}")
                    continue
                
                code_link, dataset_link, model_link = parts
                
                # Create Code object only if URL exists
                code = None
                if code_link:
                    code_type = classify_url(code_link)
                    # print(code_type)
                    if code_type == 'github' or code_type == 'gitlab' or code_type == 'hfspace':
                        code = Code(code_link)
                        populate_code_info(code, code_type)
                    else:
                        logger.warning(f"Warning: Code link on line {line_num} is not a GitHub URL: {code_link}")
                
                # Create Dataset object only if URL exists
                dataset = None
                if dataset_link:
                    dataset_type = classify_url(dataset_link)
                    if dataset_type == 'dataset':
                        dataset = Dataset(dataset_link)
                        populate_dataset_info(dataset)
                        dataset_registry[dataset._name] = dataset  # Add to registry
                    elif dataset_type == 'check':
                        is_dataset, dataset_name = is_dataset_url_llm(dataset_link)
                        if is_dataset:
                            dataset = Dataset(dataset_link)
                            dataset._name = dataset_name
                            dataset_registry[dataset._name] = dataset  # Add to registry
                        else:
                            logger.warning(f"Warning: Dataset link on line {line_num} is not a dataset according to LLM: {dataset_link}")
                    else:
                        logger.warning(f"Warning: Dataset link on line {line_num} is not valid: {dataset_link}")
                
                # Create Model object (always required)
                if not model_link:
                    logger.warning(f"Warning: Model link is missing on line {line_num}")
                    continue
                
                model_type = classify_url(model_link)
                if model_type != 'model':
                    logger.warning(f"Warning: Model link on line {line_num} is not a HuggingFace model URL: {model_link}")
                    continue
                
                # Create and populate Model object
                model = Model(model_link)
                populate_model_info(model)
                
                # Link Code and Dataset to Model (can be None/void)
                if code:
                    model.linkCode(code)
                
                if dataset:
                    model.linkDataset(dataset)
                
                models.append(model)
                
    except FileNotFoundError:
        logger.error(f"Error: File {file_path} not found")
        return [], {}
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return [], {}
    
    return models, dataset_registry


def print_model_summary(models: List[Model], dataset_registry: Dict[str, Dataset]) -> None:
    """
    Print a summary of parsed models and dataset registry for debugging
    
    Args:
        models (List[Model]): List of Model objects
        dataset_registry (Dict[str, Dataset]): Registry of all datasets
    """
    logger.debug(f"\nParsed {len(models)} models:")
    
    for i, model in enumerate(models, 1):
        logger.debug(f"Model {i}: {model.name}")
        logger.debug(f"  URL: {model.url}")
        logger.debug(f"  Code: {model.code._name if model.code else 'None (void)'}")
        logger.debug(f"  Dataset: {model.dataset._name if model.dataset else 'None (void)'}\n")
    
    logger.debug(f"\nDataset Registry ({len(dataset_registry)} datasets):")
    for name, dataset in dataset_registry.items():
        logger.debug(f"  {name}: {dataset._url}")


# if __name__ == "__main__":
#     # Test the URL parser
#     # Note: Run this from the project root directory: python3 -m utils.url_parser
#     # print(is_dataset_url_llm(" https://www.image-net.org/"))

#     import os
#     content = """https://github.com/google-research/bert, https://huggingface.co/datasets/bookcorpus/bookcorpus, https://huggingface.co/google-bert/bert-base-uncased
#     ,,https://huggingface.co/parvk11/audience_classifier_model
#     ,,https://huggingface.co/openai/whisper-tiny/tree/main
#     ,https://www.image-net.org/,https://huggingface.co/google-bert/bert-base-uncased
#     """

#     temp_path = "temp_test.txt"

#     try:
#         print(f"--- Creating temporary file: {temp_path} ---")
#         with open(temp_path, "w") as f:
#             f.write(content.strip())
#         models, dataset_registry = parse_URL_file(temp_path)

#         for i, model in enumerate(models, 1):
#             code_name = model.code._name if model.code else 'None'
#             dataset_name = model.dataset._name if model.dataset else 'None'
#             print(f"  Model {i}: {model.id} (Code: {code_name}, Dataset: {dataset_name})")
        
#         print(f"\nFound {len(dataset_registry)} unique datasets in the registry.")

#     finally:
#         if os.path.exists(temp_path):
#             os.remove(temp_path)
#             print(f"\n--- Cleaned up temporary file: {temp_path} ---")
