from typing import Any, Dict
from apis import git_api
import logging
import os
import requests

logger = logging.getLogger("api")

GEN_AI_STUDIO_API_KEY = os.getenv("GEN_AI_STUDIO_API_KEY")

# Parse the API key if it's a JSON string from AWS Secrets Manager
if GEN_AI_STUDIO_API_KEY:
    try:
        # If it's a JSON string, extract the actual key
        if GEN_AI_STUDIO_API_KEY.startswith("{"):   
            import json
            parsed = json.loads(GEN_AI_STUDIO_API_KEY)
            GEN_AI_STUDIO_API_KEY = parsed.get("GEN_AI_STUDIO_API_KEY", GEN_AI_STUDIO_API_KEY)
        
        logger.info(f"API key loaded successfully, length: {len(GEN_AI_STUDIO_API_KEY)}")
    except (json.JSONDecodeError, AttributeError) as e:
        logger.warning(f"Error parsing API key: {e}")
else:
    logger.warning("API key not found")

PURDUE_GENAI_URL = "https://genai.rcac.purdue.edu/api/chat/completions"


def get_genai_metric_data(model_url: str, prompt: str) -> Dict[str, Any]:
    """Call a GenAI endpoint with a prompt + model_url and return the parsed metric.

    Returns a dict with at least 'metric' (string) on success, otherwise an empty dict.
    This keeps the shape similar to other data_fetcher helpers.
    """
    if not GEN_AI_STUDIO_API_KEY:
        logger.debug("GEN AI API key not set; skipping GenAI call")
        return {}

    headers = {
        "Authorization": f"Bearer {GEN_AI_STUDIO_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": "llama3.1:latest",
        "messages": [
            {"role": "user", "content": prompt + " " + model_url}
        ],
    }

    try:
        resp = requests.post(
            PURDUE_GENAI_URL, headers=headers, json=body, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        metric = data.get("choices", [{}])[0].get(
            "message", {}).get("content", "").strip()
        return {"metric": metric}
    except Exception as e:
        logger.debug


def get_genai_bus_factor(model_url: str, code_url: str, repo_meta: dict = None) -> float:
    """
    Compute bus factor using GenAI LLM analysis, fallback to heuristic if needed.
    Returns a score in [0, 1].
    """
    import re
    try:
        target_url = model_url or code_url
        if not target_url:
            raise ValueError("No URL provided for GenAI analysis.")
        prompt = """Analyze the bus factor for this model/repository by examining READMEs, documentation, and contributor distribution.

Bus factor measures how well knowledge and contributions are distributed:
- High bus factor (closer to 1.0) = Knowledge is well-distributed, good documentation, builds on established research
- Low bus factor (closer to 0.0) = Knowledge is concentrated, poor documentation, requires specialized knowledge

Consider:
1. How well the README/documentation references existing research
2. Whether the approach builds on established methods
3. How accessible the knowledge is to new contributors
4. Documentation quality and completeness
5. Overlap with well-known techniques and papers

Return only a decimal number between 0.0 and 1.0 representing bus factor score.
URL:"""
        response = get_genai_metric_data(target_url, prompt)
        if response:
            match = re.search(r'(\d+\.\d+)', str(response))
            if match:
                score = float(match.group(1))
                score = max(0.5, min(1.0, score))  # Clamp to [0.5, 1.0]
                if 0.0 <= score <= 1.0:
                    return score
                if 1.0 < score <= 100.0:
                    return min(1.0, score / 100.0)
        # Fallback if extraction fails
        raise ValueError("GenAI extraction failed.")
    except Exception:
        # Heuristic fallback
        return 0.5
        # top_pct = float((repo_meta or {}).get("top_contributor_pct", 1.0))
        # return min(1.0, max(0.0, 1.0 - top_pct))


def get_hf_bus_factor(model_id: str) -> float:
    repo_info = git_api.get_repo_info_from_hf(model_id)
    if not repo_info or 'owner' not in repo_info or 'repo' not in repo_info:
        return 0.0
    owner = repo_info['owner']
    repo = repo_info['repo']
    return bus_factor(f"{owner}/{repo}", "github")



def bus_factor(model_url, code_url, id: str, code_type: str) -> float:
    """
    Calculate the bus factor of a repository.
    The bus factor is defined as the minimum number of developers that need to be incapacitated
    (e.g., hit by a bus) before the project is in serious trouble.

    Sort contributors by commits, add them up until you cover at least 50% of total commits.
    The bus factor is then the number of contributors needed to reach that 50% threshold divided by
    the total number of contributors.

    Args:
        owner (str): The owner of the repository.
        repo (str): The repository identifier.

    Returns:
        float: The bus factor of the repository. [0-1]
    """
    if code_type != "github":
        #phase 1 update
        return get_genai_bus_factor(model_url, code_url, None)
    contributors = git_api.get_contributors(id)
    # Handle edge cases
    if not contributors:
        return 0
    elif len(contributors) == 1:
        return 1

    raw_bus_factor = 0
    total_commits = sum(contributor['contributions'] for contributor in contributors)
    sorted_contributors = sorted(contributors, key=lambda x: x['contributions'], reverse=True)
    cumulative_commits = 0
    for contributor in sorted_contributors:
        cumulative_commits += contributor['contributions']
        raw_bus_factor += 1
        if cumulative_commits >= total_commits / 2:
            break
    score = raw_bus_factor/len(contributors)
    bus_factor = 1 - score
    
    return bus_factor


# if __name__ == "__main__":
#     # Case 1: Major open source repo
#     owner = "google-bert"
#     repo = "bert-base-uncased"
#     print(f"Bus Factor for {owner}/{repo}: {bus_factor(owner, repo)}")

    # # Case 2: Small open source repo (us)
    # owner = "ECE461ProjTeam"
    # repo = "ModelReuseCLI"
    # print(f"Bus Factor for {owner}/{repo}: {bus_factor(owner, repo)}")

    # # Case 3: Repo with 2 contributors
    # owner = "octocat"
    # repo = "Hello-World"
    # print(f"Bus Factor for {owner}/{repo}: {bus_factor(owner, repo)}")
    
    # # Case 4: Repo with one contributor
    # owner = "vdudhaiy"
    # repo = "llmrec-570-copy"
    # print(f"Bus Factor for {owner}/{repo}: {bus_factor(owner, repo)}")
