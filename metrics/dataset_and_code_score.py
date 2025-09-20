from huggingface_hub import HfFileSystem
from apis.hf_client import HFClient
from apis.git_api import *


def dataset_and_code_score(model_id, dataset_id, code_id):
    fs = HfFileSystem()
    client = HFClient()

    headers = set_git_headers()
    files_request = make_request(f"https://api.github.com/repos/{code_id}/git/trees/master?recursive=1", headers).json()
    code_files = [item["path"] for item in files_request["tree"]]

    # if the model has a dataset and code linked it gets some score by default
    score = 0.25

    dataset_files_raw = fs.ls("datasets/" + dataset_id)
    ds_files = [file["name"][file["name"].index(dataset_id) + len(dataset_id) + 1: ] for file in dataset_files_raw]
    # model_card = client.model_card_text(model_id)
    if "README.md" in ds_files:
        score += 0.25
    if "requirements.txt" in code_files:
        score += 0.1
    for file in code_files:
        if "test" in file:
            score += 0.15
            break
    if "README.md" in code_files:
        score += 0.25
    
    return score

