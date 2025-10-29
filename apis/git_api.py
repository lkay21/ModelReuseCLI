import os
import requests
import time
from typing import List, Dict, Any, Optional
import logging
import json
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, retry_if_result


logger = logging.getLogger('cli_logger')


# For Testing: Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()  # reads .env file into environment variables
# REMOVE ABOVE LINES IN PRODUCTION


def check_git_token() -> Optional[str]:
    '''
    Check for a GitHub token in the environment variables and return it if found.
    If not found, check for a txt file named 'git_token.txt' in the current directory and read the token from there.
    If still not found, return None.
    '''
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        try:
            with open("git_token.txt", "r") as f:
                token = f.read().strip()
        except FileNotFoundError:
            logger.warning("GitHub token not found in environment variables or 'git_token.txt' file.")
            return None
    return token


@retry(
    retry=(
        retry_if_exception_type((requests.exceptions.RequestException, json.JSONDecodeError, Exception)) |
        retry_if_result(lambda result: result is None)
    ),
    wait=wait_exponential(multiplier=1, max=10),
    stop=stop_after_attempt(3)
)
def make_request(url: str, headers: Dict[str, str], max_time: int = 60) -> requests.Response:
    '''
    Make a GET request to the specified URL with the provided headers, handling rate limiting and retries
    using exponential backoff.
    Default wait time starts at 1 second and doubles with each retry up to a maximum of 60 seconds.

    Args:
        url (str): The URL to send the GET request to.
        headers (Dict[str, str]): Headers to include in the request.
        max_time (int): Maximum time to wait for retries in seconds.
    Returns:
        requests.Response: The response object from the GET request.'''
    wait_time = 1

    while wait_time <= 60:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response
        elif (
            response.status_code == 403
            and 'X-RateLimit-Remaining' in response.headers
            and response.headers['X-RateLimit-Remaining'] == '0'
        ):
            reset_time = int(response.headers.get('X-RateLimit-Reset', time.time() + wait_time))
            sleep_time = max(reset_time - time.time(), wait_time)
            logger.warning(f"Rate limit exceeded. Sleeping for {sleep_time} seconds.")
            time.sleep(sleep_time)
        else:
            logger.warning(f"Request failed with status code {response.status_code}. Retrying in {wait_time} seconds.")
            time.sleep(wait_time)
            wait_time *= 2

    logger.error(f"Failed to fetch data from {url} after multiple attempts.")
    # raise Exception(f"Failed to fetch data from {url} after multiple attempts.")


def set_git_headers() -> Dict[str, str]:
    '''Set headers for GitHub API requests, specifically authorization if a token is set in the environment variables.'''
    token = check_git_token()
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def get_contributors(id: str) -> List[Dict[str, Any]]:
    """
    Retrieve contributors from a GitHub repository.

    Args:
        owner (str): Repository owner (e.g., "octocat")
        repo (str): Repository name (e.g., "hello-world")

    Returns:
        list: A list of contributor objects (dicts) from the GitHub API
    """
    headers = set_git_headers()
    url = f"https://api.github.com/repos/{id}/contributors"
    response = make_request(url, headers)
    return response.json()


# if __name__ == "__main__":
#     # Sample Output
#     id = "google-research/bert"
#     contributers = get_contributors(id)
#     print("Contributors:")
#     for contributor in contributers:
#         print(f"Contributor: {contributor['login']} - Contributions: {contributor['contributions']}")
    # commits = get_commit_history(owner, repo)
    # print("\nCommits:")
    # for commit in commits:
    #     print(f"Commit: {commit['sha']} - {commit['commit']['message']}")
    #     print(f"Author: {commit['commit']['author']['name']} <{commit['commit']['author']['email']}>")
