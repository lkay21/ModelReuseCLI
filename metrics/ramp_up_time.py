from __future__ import annotations
import os
from typing import Dict, Any

from apis.hf_client import HFClient


def _clamp01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def ramp_up_time(model_id: str) -> Dict[str, Any]:
    """
    Ramp-up score from README + HF metadata (regex-free) with optional LLM blend.
    Returns: {'score': float in [0,1]}
    """
    # --- fetch HF data ---
    hf = HFClient()
    hf_info = hf.model_info(model_id) or {}
    card_text = (hf.model_card_text(model_id) or "").strip()
    low = card_text.lower()

    # --- simple heuristic cues ---
    has_readme     = 1 if card_text else 0
    has_quickstart = 1 if any(k in low for k in [
        "getting started", "quick start", "quickstart", "usage", "how to use", "how-to-use"
    ]) else 0
    has_install    = 1 if any(k in low for k in [
        "pip install ", "pip3 install ", "conda install ", "poetry add ", "requirements.txt"
    ]) else 0
    has_example    = 1 if any(k in card_text for k in [
        "from transformers import", "pipeline("
    ]) else 0
    has_meta       = 1 if any(hf_info.get(k) for k in ("pipeline_tag", "tags", "cardData")) else 0

    heur_score = (
        0.10 * has_readme +
        0.25 * has_quickstart +
        0.20 * has_install +
        0.25 * has_example +
        0.20 * has_meta
    )
    score = _clamp01(heur_score)

    # LLM blend (70% heuristics, 30% Gemini) 
    # lazy import; prefer get_gemini_key() from apis.gemini if available
    key = os.getenv("GEMINI_API_KEY")
    _pg = None
    try:
        from apis.gemini import get_gemini_key, prompt_gemini as _pg  
        key = get_gemini_key() or key
    except Exception:
        pass  

    if key and _pg and card_text:
        prompt = (
            "Grade how easy it is to start using a model from this README.\n"
            "Return ONLY a float in [0,1].\n"
            "1.0 = clear quickstart, install command, minimal runnable example.\n"
            "0.0 = academic or unclear with no quickstart.\n\nREADME:\n"
            f"{card_text[:6000]}\n\nJust the number:"
        )
        txt = (_pg(prompt, key) or "").strip()
        llm_score = None
        for tok in txt.replace(",", " ").split():
            try:
                llm_score = _clamp01(float(tok))
                break
            except Exception:
                continue
        if llm_score is not None:
            score = _clamp01(0.7 * heur_score + 0.3 * llm_score)

    return {"score": score}


if __name__ == "__main__":
    print(ramp_up_time("bert-base-uncased"))

