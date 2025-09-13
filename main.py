#!/usr/bin/env python3
import argparse
import sys
import os

from apis.gemini import prompt_gemini
from apis.hf_client import HFClient, resolve_hf_token


def install_dependencies():
    print("Installing dependencies...")
    success = os.system("pip install -r requirements.txt")
    sys.exit(-1 if success else 0)


def get_api_keys():
    """
    Compile all available API keys into a dictionary.

    Returns:
        keys (dict): Dictionary of API keys with service names as keys
    """
    keys = {}

    try:
        with open('gemini_key.txt', 'r') as file:
            gemini_api_key = file.readline().strip()
        keys.update({'gemini': gemini_api_key})
    except FileNotFoundError:
        print("API key file not found. Please create 'gemini_key.txt' with your Gemini API key.")
        sys.exit(-1)

    # Hugging Face
    hf_token = resolve_hf_token()
    if hf_token:
        keys.update({'huggingface': hf_token})

    return keys


def run_hf_test():
    """Simple smoke test for Hugging Face integration."""
    print("Running Hugging Face smoke test...")
    hf = HFClient()

    m = hf.model_info("bert-base-uncased")
    d = hf.dataset_info("rajpurkar/squad")
    card = hf.model_card_text("bert-base-uncased")

    print("model ok:", bool(m), "modelId:", m.get("modelId"))
    print("dataset ok:", bool(d), "id:", d.get("id"))
    print("card text chars:", len(card or ""))


def main():
    parser = argparse.ArgumentParser(description="ModelReuseCLI main entry point")
    parser.add_argument('option', type=str, help="'install', 'hf-test', or URL_FILE")
    args = parser.parse_args()

    if args.option == "install":
        install_dependencies()
    elif args.option == "hf-test":
        run_hf_test()
    else:
        url_file = args.option
        # add processing here


if __name__ == "__main__":
    main()

