from __future__ import annotations
import os
from apis.hf_client import HFClient
from utils.prompt_key import get_prompt_key
from apis.gemini import prompt_gemini, get_gemini_key
from apis.purdue_genai import prompt_purdue_genai, get_purdue_genai_key
from typing import Dict, Any
import logging
import math


def _clamp01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def extract_hf_model_id(hf_url: str) -> Optional[str]:
    """Extract the canonical repo_id for HF (model or dataset)."""
    try:
        if "huggingface.co" not in hf_url:
            return None

        path = urlparse(hf_url).path.strip("/")
        parts = path.split("/")

        # datasets/<id>  OR  datasets/<owner>/<name>
        if parts and parts[0] == "datasets":
            if len(parts) == 2:
                # e.g., https://huggingface.co/datasets/glue  -> "glue"
                return parts[1]
            elif len(parts) >= 3:
                # e.g., https://huggingface.co/datasets/user/name ->
                # "user/name"
                return f"{parts[1]}/{parts[2]}"

        # model URLs can be:
        # - <owner>/<name> (e.g., facebook/bart-base)
        # - <name> (e.g., bert-base-uncased - legacy format)
        if len(parts) >= 2:
            return f"{parts[0]}/{parts[1]}"
        elif len(parts) == 1:
            # Handle legacy single-name models like bert-base-uncased
            return parts[0]
    except Exception:
        pass
    return None


def get_huggingface_model_data(model_url: str) -> Dict[str, Any]:
    """Fetch HF model metadata via the Hub API."""
    try:
        from huggingface_hub import HfApi, model_info

        model_id = extract_hf_model_id(model_url)
        if not model_id:
            return {}

        info = model_info(model_id)
        api = HfApi()

        data: Dict[str, Any] = {
            "license": None,
            "tags": getattr(info, "tags", []) or [],
            "downloads": getattr(info, "downloads", 0) or 0,
            "pipeline_tag": getattr(info, "pipeline_tag", None),
            "model_id": getattr(info, "modelId", model_id),
            "sha": getattr(info, "sha", None),
            "card_data": getattr(info, "cardData", {}) or {},
        }
        if data["card_data"]:
            data["license"] = data["card_data"].get("license", "")

        # total size (best-effort)
        total_size = 0
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
        data["total_size_bytes"] = total_size
        return data
    except Exception as e:
        # logger.debug(f"Failed to fetch HF model data: {e}")
        return {}
    
def normalize_downloads(downloads: int) -> float:
    if downloads <= 0:
        return 0.0
    return min(1.0, math.log10(max(downloads, 1)) / 6.0)  # 1e6 -> 1.0

def ramp_up_time(model_url: str) -> float:
# def ramp_up_time(model_id: str) -> float:
    """
    Ramp-up score from README + HF metadata (regex-free) with optional LLM blend.
    Returns: {'score': float in [0,1]}
    """

    hf_m = get_huggingface_model_data(model_url)

    downloads = int(hf_m.get("downloads", 0) or 0)

    ramp = {}
    ramp["downloads_norm"] = normalize_downloads(downloads)
    # HF likes not exposed consistently
    ramp["likes_norm"] = 0.5
    # default; refined by GitHub below
    ramp["recency_norm"] = 0.7

    vals = [float(ramp[k]) for k in ("likes_norm", "downloads_norm", "recency_norm") if k in ramp]
    value = sum(vals) / len(vals) if vals else 0.0
    # --- fetch HF data ---
    # hf = HFClient()
    # hf_info = hf.model_info(model_id) or {}
    # card_text = (hf.model_card_text(model_id) or "").strip()
    # low = card_text.lower()

    # # --- simple heuristic cues ---
    # has_readme     = 1 if card_text else 0
    # has_quickstart = 1 if any(k in low for k in [
    #     "getting started", "quick start", "quickstart", "usage", "how to use", "how-to-use"
    # ]) else 0
    # has_install    = 1 if any(k in low for k in [
    #     "pip install ", "pip3 install ", "conda install ", "poetry add ", "requirements.txt"
    # ]) else 0
    # has_example    = 1 if any(k in card_text for k in [
    #     "from transformers import", "pipeline("
    # ]) else 0
    # has_meta       = 1 if any(hf_info.get(k) for k in ("pipeline_tag", "tags", "cardData")) else 0

    # heur_score = (
    #     0.10 * has_readme +
    #     0.25 * has_quickstart +
    #     0.20 * has_install +
    #     0.25 * has_example +
    #     0.20 * has_meta
    # )
    # score = _clamp01(heur_score)

    # # LLM blend (70% heuristics, 30% Gemini) 
    # # lazy import; prefer get_gemini_key() from apis.gemini if available
    # prompt_key = get_prompt_key()
    # if 'purdue_genai' in prompt_key:
    #     prompt_function = prompt_purdue_genai
    #     api_key = get_purdue_genai_key()
    # elif 'gemini' in prompt_key:
    #     prompt_function = prompt_gemini
    #     api_key = get_gemini_key()

    # if api_key and prompt_function and card_text:
    #     prompt = (
    #         "Grade how easy it is to start using a model from this README.\n"
    #         "Return ONLY a float in [0,1].\n"
    #         "1.0 = clear quickstart, install command, minimal runnable example.\n"
    #         "0.0 = academic or unclear with no quickstart.\n\nREADME:\n"
    #         f"{card_text[:6000]}\n\nJust the number:"
    #     )
    #     txt = (prompt_function(prompt, api_key) or "").strip()
    #     llm_score = None
    #     for tok in txt.replace(",", " ").split():
    #         try:
    #             llm_score = _clamp01(float(tok))
    #             break
    #         except Exception:
    #             continue
    #     if llm_score is not None:
    #         score = _clamp01(0.7 * heur_score + 0.3 * llm_score)

    # return score
    return value


# if __name__ == "__main__":
#     print(ramp_up_time("bert-base-uncased"))

