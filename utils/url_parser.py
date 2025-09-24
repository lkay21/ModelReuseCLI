"""
URL Parser for ModelReuseCLI
Handles parsing URL files and creating Model, Code, Dataset objects
"""

import re
from typing import List, Tuple, Dict
from model import Model, Code, Dataset


def classify_url(url: str) -> str:
    """
    Classify a URL by its type
    
    Args:
        url (str): The URL to classify
        
    Returns:
        str: 'code', 'dataset', 'model', or 'unknown'
    """
    if not url or not url.strip():
        return 'unknown'
    
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
    
    return 'unknown'


def extract_name_from_url(url: str) -> str:
    """
    Extract a name from a URL
    
    Args:
        url (str): The URL
        
    Returns:
        str: Extracted name or empty string if extraction fails
    """
    if not url:
        return ""
    
    # code pattern: github/gitlab/hfspace
    github_match = re.search(r'github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/.*)?$', url, re.IGNORECASE)
    if github_match:
        owner, repo = github_match.groups()
        return repo.replace('.git', '')

    gitlab_match = re.search(r'(?:git@|https?://)gitlab\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?$', url, re.IGNORECASE)
    if gitlab_match:
        return gitlab_match.group('repo')

    hfcode_match = re.search(r'^https?://(?:www\.)?huggingface\.co/spaces/(?P<owner>[^/]+)/(?P<space>[^/]+)(?:/.*)?$', url, re.IGNORECASE)
    if hfcode_match:
        return hfcode_match.group('space')

    # HuggingFace pattern: extract model/dataset name
    # HuggingFace dataset pattern: huggingface.co/datasets/namespace/name
    hf_dataset_match = re.search(r'huggingface\.co/datasets/([^/]+)/([^/]+?)(?:/.*)?$', url, re.IGNORECASE)
    if hf_dataset_match:
        namespace, name = hf_dataset_match.groups()
        return f"{namespace}/{name}"

    # HuggingFace model pattern: handle both single and double segment formats
    # Two segments: huggingface.co/namespace/modelname
    hf_model_two_match = re.search(r'huggingface\.co/([^/]+)/([^/]+?)(?:/.*)?$', url, re.IGNORECASE)
    if hf_model_two_match:
        namespace, name = hf_model_two_match.groups()
        return name
    
    # Single segment: huggingface.co/modelname
    hf_model_one_match = re.search(r'huggingface\.co/([^/]+?)(?:/.*)?$', url, re.IGNORECASE)
    if hf_model_one_match:
        name = hf_model_one_match.group(1)
        return name
    
    return ""


def populate_code_info(code: Code, code_type: str) -> None:
    """
    Populate Code object with additional information from GitHub API
    
    Args:
        code (Code): Code object to populate
    """
    # Extract name from URL
    code._name = extract_name_from_url(code._url)
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
    dataset._id = extract_name_from_url(dataset._url)
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
    model.name = extract_name_from_url(model.url)
    # TODO: Add HuggingFace API calls to populate hfAPIData
    # Example implementation for metrics teams:
    # from apis.hf_client import HFClient
    # hf_client = HFClient()
    # model.hfAPIData = {
    #     'model_info': hf_client.model_info(model.name),
    #     'downloads': ..., 'license': ..., 'size': ...
    # }


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
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()

                # Parse the CSV line
                parts = [part.strip() for part in line.split(',')]
                
                # Ensure we have exactly 3 parts
                if len(parts) != 3:
                    print(f"Warning: Line {line_num} does not have exactly 3 columns: {line}")
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
                        print(f"Warning: Code link on line {line_num} is unknown: {code_link}")
                
                # Create Dataset object only if URL exists
                dataset = None
                if dataset_link:
                    dataset_type = classify_url(dataset_link)
                    if dataset_type == 'dataset':
                        dataset = Dataset(dataset_link)
                        populate_dataset_info(dataset)
                        dataset_registry[dataset._name] = dataset  # Add to registry
                    else:
                        print(f"Warning: Dataset link on line {line_num} is not a HuggingFace dataset URL: {dataset_link}")
                
                # Create Model object (always required)
                if not model_link:
                    print(f"Warning: Model link is missing on line {line_num}")
                    continue
                
                model_type = classify_url(model_link)
                if model_type != 'model':
                    print(f"Warning: Model link on line {line_num} is not a HuggingFace model URL: {model_link}")
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
        print(f"Error: File {file_path} not found")
        return [], {}
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return [], {}
    
    return models, dataset_registry


def print_model_summary(models: List[Model], dataset_registry: Dict[str, Dataset]) -> None:
    """
    Print a summary of parsed models and dataset registry for debugging
    
    Args:
        models (List[Model]): List of Model objects
        dataset_registry (Dict[str, Dataset]): Registry of all datasets
    """
    print(f"\nParsed {len(models)} models:")
    
    for i, model in enumerate(models, 1):
        print(f"Model {i}: {model.name}")
        print(f"  URL: {model.url}")
        print(f"  Code: {model.code._name if model.code else 'None (void)'}")
        print(f"  Dataset: {model.dataset._name if model.dataset else 'None (void)'}\n")
    
    print(f"\nDataset Registry ({len(dataset_registry)} datasets):")
    for name, dataset in dataset_registry.items():
        print(f"  {name}: {dataset._url}")
    print()


if __name__ == "__main__":
    # Test the URL parser
    # Note: Run this from the project root directory: python3 -m utils.url_parser
    nametest_cases = [
        # GitHub URLs
        ("https://github.com/google-research/bert", "bert"),
        ("https://github.com/user/my-repo.git", "my-repo"),
        
        # GitLab URLs
        ("https://gitlab.com/user/awesome-project", "awesome-project"),
        ("git@gitlab.com:user/cool-app.git", "cool-app"),
        
        # HuggingFace Spaces
        ("https://huggingface.co/spaces/abidlabs/en2fr", "en2fr"),
        ("https://huggingface.co/spaces/microsoft/DialoGPT-medium", "DialoGPT-medium"),

        # Model URLs
        ("https://huggingface.co/roberta-base", "roberta-base"),
        ("https://huggingface.co/distilbert-base-uncased", "distilbert-base-uncased")
    ]

    print(extract_name_from_url("https://huggingface.co/roberta-base"))
    print(extract_name_from_url("https://huggingface.co/distilbert-base-uncased"))

    # for url, expected_name in nametest_cases:
    #     extracted_name = extract_name_from_url(url)
    #     assert extracted_name == expected_name, f"Failed for {url}: expected {expected_name}, got {extracted_name}"
    #     print(f"Passed: {url} -> {extracted_name}")
