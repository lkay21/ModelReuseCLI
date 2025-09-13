from __future__ import annotations

import os
from typing import Any, Dict, Optional
from huggingface_hub import HfApi, HfFolder, ModelCard, DatasetCard

HF_ENV = "HF_TOKEN"


def resolve_hf_token() -> Optional[str]:
    token = os.getenv(HF_ENV)
    if token:
        return token

    key_path = "hf_key.txt"
    if os.path.exists(key_path):
        with open(key_path, "r", encoding="utf-8") as f:
            token = f.readline().strip() or None
    return token


class HFClient:
    def __init__(self):
        token = resolve_hf_token()
        if token:
            # Save so huggingface_hub picks it up automatically
            HfFolder.save_token(token)
        self.api = HfApi()

    #Models 
    def model_info(self, model_id: str) -> Dict[str, Any]:
        try:
            info = self.api.model_info(model_id)
            return getattr(info, "__dict__", {}) or {}
        except Exception:
            return {}

    def model_card_text(self, model_id: str) -> Optional[str]:
        try:
            card = ModelCard.load(model_id)
            return getattr(card, "text", None)
        except Exception:
            return None

    #Datasets
    def dataset_info(self, dataset_id: str) -> Dict[str, Any]:
        try:
            info = self.api.dataset_info(dataset_id)
            return getattr(info, "__dict__", {}) or {}
        except Exception:
            return {}

    def dataset_card_text(self, dataset_id: str) -> Optional[str]:
        try:
            card = DatasetCard.load(dataset_id)
            return getattr(card, "text", None)
        except Exception:
            return None
