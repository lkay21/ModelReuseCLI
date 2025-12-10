from huggingface_hub import HfFileSystem
from apis.hf_client import HFClient
from apis.git_api import *



def check_availability(code_url: str, dataset_url: str,
                       model_url: str) -> Dict[str, Any]:
    """HEAD the URLs and report availability of each and overall links_ok."""
    results = {"has_code": False, "has_dataset": False,
               "has_model": False, "links_ok": False}
    urls = [("code", code_url), ("dataset", dataset_url), ("model", model_url)]
    ok = 0
    for name, url in urls:
        if url and url.strip():
            try:
                r = requests.head(url, timeout=10, allow_redirects=True)
                good = r.status_code in (200, 301, 302)
                results[f"has_{name}"] = good
                ok += int(good)
            except Exception as e:
                logger.debug(f"Failed to check {name} URL {url}: {e}")
                results[f"has_{name}"] = False
        else:
            results[f"has_{name}"] = False
    results["links_ok"] = ok >= 2
    return results


def dataset_and_code_score(dataset_url: str, code_url: str, model_url: str) -> float:
# def dataset_and_code_score(dataset_id: str, code_id: str, code_type: str) -> float:

    # fs = HfFileSystem()
    # client = HFClient()
    # headers = set_git_headers()
    
    # score = 0
    # code_files = []
    
    # if (dataset_id):
    #     score += 0.125
    #     try:
    #         dataset_files_raw = fs.ls("datasets/" + dataset_id)
    #         ds_files = [file["name"][file["name"].index(dataset_id) + len(dataset_id) + 1: ] for file in dataset_files_raw]
    #         if "README.md" in ds_files:
    #             score += 0.25
    #     except:
    #         pass

    # if(code_id):
    #     score += 0.125
    #     if code_type == "github":
    #         files_request = make_request(f"https://api.github.com/repos/{code_id}/git/trees/master?recursive=1", headers).json()
    #         code_files = [item["path"] for item in files_request["tree"]]
    #     elif code_type == "gitlab":
    #         # files_request = make_request(f"https://gitlab.example.com/api/v4/projects/{code_id}/repository/tree", headers).json()
    #         code_files = []
    #         # idk how to do requests to gitlab!!
        
    #     if "requirements.txt" in code_files:
    #         score += 0.1
    #     for file in code_files:
    #         if "test" in file:
    #             score += 0.15
    #             break
    #     if "README.md" in code_files:
    #         score += 0.25

    availability = check_availability(code_url, dataset_url, model_url)

    has_code = availability.get("has_code", False)
    has_dataset = availability.get("has_dataset", False) 
    links_ok = availability.get("links_ok", False)
    
    # Calculate value as average of the three components
    components = [has_code, has_dataset, links_ok]
    value = sum(components) / len(components)
    
    return value

