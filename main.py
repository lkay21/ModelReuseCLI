#!/usr/bin/env python3
import argparse
import sys
import os
from typing import Dict
import json
import logging
import zipfile

from utils.url_parser import parse_URL_file, print_model_summary
from utils.logger import setup_logger
from utils.prompt_key import get_prompt_key
from utils.env_check import check_environment
from typing import Dict
from apis.gemini import *
from apis.purdue_genai import *
from apis.hf_client import resolve_hf_token

# For Testing: Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()  # reads .env file into environment variables
# REMOVE ABOVE LINES IN PRODUCTION



def main():
    if not check_environment():
        sys.exit(1)

    setup_logger()  # configure logging once
    logger = logging.getLogger('cli_logger')
    
    logger.info("Starting ModelReuseCLI...")
    parser = argparse.ArgumentParser(description="ModelReuseCLI main entry point")
    parser.add_argument('url_file', type=str, help="Path to URL_FILE for analysis")
    args = parser.parse_args()

    # Treat as URL_FILE path
    url_file = args.url_file
    
    # Check if the file exists
    if not os.path.exists(url_file):
        logger.error(f"Error: File '{url_file}' not found.")
        sys.exit(1)

    # Check if file is zip file
    if zipfile.is_zipfile(url_file):
        is_zipped = True
        logger.info(f"File '{url_file}' is a zip file.")
    else:
        is_zipped = False
        logger.warning(f"File '{url_file}' is not a zip file.")

    # Ensure LLM tokens are present by attempting to get the keys
    get_prompt_key()
    
    # Parse the URL file and create Model objects
    models, dataset_registry = parse_URL_file(url_file, is_zipped)
    
    if not models:
        logger.error("No models found in the file.")
        sys.exit(1)
    
    # Print summary of parsed models
    print_model_summary(models, dataset_registry)
    
    logger.debug("\nURL parsing complete! Created:")
    logger.debug(f"  - {len(models)} Model objects")
    logger.debug(f"  - {len(dataset_registry)} unique datasets")
    logger.info("Objects ready for metric calculation teams.")
    for model in models:
        print(json.dumps(model.evaluate()))


if __name__ == "__main__":
    main()