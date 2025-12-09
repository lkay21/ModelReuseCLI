from huggingface_hub import HfApi
from apis.hf_client import HFClient
from math import log10
from typing import Dict
import logging

#Changed raspberry pi limit to 1B
PLATFORM_SIZE_LIMITS = {"raspberry_pi": 1, "jetson_nano": 7, "desktop_pc": 34, "aws_server": 1200}
LOWER_SIZE_LIMIT = 0.01

logger = logging.getLogger("api")

# total_size = 0
#         try:
#             files = api.list_repo_files(model_id, repo_type="model")
#             for fp in files:
#                 try:
#                     fi = api.get_paths_info(model_id, fp, repo_type="model")
#                     if fi and len(fi) > 0:  # fi is a list
#                         # Get size from the first (and typically only) RepoFile
#                         # object
#                         size = fi[0].size
#                         if size:
#                             total_size += int(size)
#                 except Exception:
#                     continue
#         except Exception: 
#             pass
#         data["total_size_bytes"] = total_size

def get_size(model_id: str) -> int:
    total_size = 0
    api = HfApi()
    try:
        files = api.list_repo_files(model_id, repo_type="model")
        for fp in files:
            try:
                fi = api.get_paths_info(model_id, fp, repo_type="model")
                if fi and len(fi) > 0:  # fi is a list
                    # Get size from the first (and typically only) RepoFile
                    # object
                    size = fi[0].size
                    if size:
                        total_size += int(size)
            except Exception:
                continue
    except Exception:
        pass
    
    return total_size
    



def size_score(model_id: str) -> Dict[str, float]:
    """Calculate a size-based score for a given model.

    Args:
        model_id (str): The id of the model to evaluate.
    Returns:
        dict: A score between 0 and 1 based on the model's size & platform.

    """


    client = HFClient()
    model_info = client.model_info(model_id)

    total_size_bytes = get_size(model_id)

    if total_size_bytes <= 0:
        result =  { "raspberry_pi": 0.01, "jetson_nano": 0.01, "desktop_pc": 0.01, "aws_server": 0.01}
    else:
        mb = 1024 * 1024
        gb = 1024 * mb
        rpi = max(0.5, min(1.0, 1.0 - (total_size_bytes / (100 * mb))))
        jetson = max(0.5, min(1.0, 1.0 - (total_size_bytes / (1 * gb))))
        desktop = max(0.5, min(1.0, 1.0 - (total_size_bytes / (10 * gb))))
        aws = max(0.5, min(1.0, 1.0 - (total_size_bytes / (100 * gb))))

        result ={"raspberry_pi": rpi, "jetson_nano": jetson, "desktop_pc": desktop, "aws_server": aws}
    
    # If no safetensors info is available, add our code to not return 0 for all platforms
    # return {plat: 0 for plat in PLATFORM_SIZE_LIMITS}

    return result



    # if 'safetensors' not in model_info.keys() or model_info["safetensors"] is None:
    #     logger.info(f"No safetensors info available for model {model_id}, using total size calculation.")
    #     total_size_bytes = get_size(model_id)

    #     if total_size_bytes <= 0:
    #         result =  { "raspberry_pi": 0.01, "jetson_nano": 0.01, "desktop_pc": 0.01, "aws_server": 0.01}
    #     else:
    #         mb = 1024 * 1024
    #         gb = 1024 * mb
    #         rpi = max(0.01, min(1.0, 1.0 - (total_size_bytes / (100 * mb))))
    #         jetson = max(0.01, min(1.0, 1.0 - (total_size_bytes / (1 * gb))))
    #         desktop = max(0.01, min(1.0, 1.0 - (total_size_bytes / (10 * gb))))
    #         aws = max(0.01, min(1.0, 1.0 - (total_size_bytes / (100 * gb))))

    #         result ={"raspberry_pi": rpi, "jetson_nano": jetson, "desktop_pc": desktop, "aws_server": aws}
        
    #     # If no safetensors info is available, add our code to not return 0 for all platforms
    #     # return {plat: 0 for plat in PLATFORM_SIZE_LIMITS}

    #     return result
    # parameters = model_info['safetensors'].total/1e9
    # result = {}
    # for plat in PLATFORM_SIZE_LIMITS:
    #     if parameters > PLATFORM_SIZE_LIMITS[plat] or parameters < LOWER_SIZE_LIMIT:
    #         result[plat] = 0.01
    #     else:
    #         score = round(log10(parameters/LOWER_SIZE_LIMIT)/log10(PLATFORM_SIZE_LIMITS[plat]/LOWER_SIZE_LIMIT), ndigits=2)
    #         result[plat] = round(max(0.01, min(1.0, score)), 2)
    # return result
    
# if __name__ == "__main__":
    
#     model_id = "deepseek-ai/DeepSeek-R1"
#     score = size_score(model_id)
#     print(score)